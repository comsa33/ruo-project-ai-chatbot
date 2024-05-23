import traceback

import pandas as pd
from icecream import ic
from sqlalchemy import create_engine, text

from app.common.core.utils import format_error_message, snake_to_camel
from app.config.settings import DEV_MARIADB_URL, CPU_MARIADB_URL
from app.config.ai_status_code import ServiceInternalError, Success
from app.common.patent.base.patent_queries import (
    patent_query,
    patent_sim_query,
    corp_info_query,
)

dev_engine = create_engine(DEV_MARIADB_URL, pool_pre_ping=True, pool_recycle=3600)
cpu_engine = create_engine(CPU_MARIADB_URL, pool_pre_ping=True, pool_recycle=3600)

# 상수 정의
SIMILARITY_THRESHOLD = 70
OK_MSG = "총 유사특허 {}개 중 유사도 {}% 이상인 특허 {}개 조회"
NO_INFO_MSG = "해당 출원번호로 조회된 정보가 존재하지 않습니다."
NO_SIMILAR_PATENT_MSG = "유사한 특허가 없습니다."
NO_CORP_INFO_MSG = "유사한 특허를 보유한 기업 정보가 없습니다."
EMPTY_RESULT_MSG = "유사한 특허를 보유한 기업에 대한 상세 기업 정보가 없습니다."
GENERAL_ERROR_MSG = "서버에러가 발생했습니다. 관리자에게 문의하세요. {}"
TOKEN_EXPIRED_MSG = "토근 기간이 만료되었습니다. 관리자에게 토큰 갱신을 요청하세요."


class PatentBuyerInfoUtils:
    def __init__(self):
        pass

    def fetch_similar_patents(self, applicate_number: str, connection) -> pd.DataFrame:
        """유사한 특허 데이터를 가져온다.
        Args:
            applicate_number: 특허 출원번호
            connection: db connection
        Returns:
            sim_df: 유사한 특허 데이터
            total_cnt: 유사한 특허 데이터 개수
        """
        sim_df = pd.read_sql(
            text(patent_sim_query), connection, params={"applicate_number": applicate_number}
        )
        total_cnt = len(sim_df)
        return sim_df, total_cnt

    def fetch_corp_info(self, patent_df: pd.DataFrame, connection) -> pd.DataFrame:
        """법인 번호에 따른 기업 정보를 가져온다.
        Args:
            patent_df: 유사한 특허의 기업 데이터
            connection: db connection
        Returns:
            corp_info_df: 법인 번호에 따른 기업 정보
        """
        corp_info_data = []
        for corp_num in patent_df["corp_num"]:
            corp_info_result = connection.execute(
                text(corp_info_query), {"corporation_num": corp_num}
                )
            corp_info_data.extend([row._asdict() for row in corp_info_result])
        return pd.DataFrame(corp_info_data)

    def fetch_and_extract_patent_data(self, sim_df: pd.DataFrame, connection) -> pd.DataFrame:
        """유사한 특허의 출원번호를 기반으로 기업 데이터를 가져온다.
        Args:
            sim_df: 유사한 특허 데이터
            connection: db connection
        Returns:
            patent_df: 유사한 특허의 기업 데이터
        """
        patent_data = []
        for _, row in sim_df.iterrows():
            sim_applicate_number = row["patent"]
            sim = row["sim"]
            patent_result = connection.execute(
                text(patent_query), {"applicate_number": sim_applicate_number}
            )
            patent_data.extend([dict(row._asdict(), sim=sim) for row in patent_result])
        return pd.DataFrame(patent_data).drop_duplicates(subset=["corp_num", "applicate_number"])

    def preprocess_patent_data(self, patent_df: pd.DataFrame) -> pd.DataFrame:
        """유사한 특허의 기업 데이터를 전처리한다. (평균 유사도, 특허 개수 기준으로 정렬)
        Args:
            patent_df: 유사한 특허의 기업 데이터
        Returns:
            patent_df: 전처리된 유사한 특허의 기업 데이터
        """
        patent_df = (
            patent_df.groupby("corp_num")
            .agg(patent_count=("applicate_number", "count"), avg_score=("sim", "mean"))
            .reset_index()
        )
        patent_df["avg_score"] = patent_df["avg_score"].round(2)
        return patent_df.sort_values(by=["avg_score", "patent_count"], ascending=False)

    def combine_data(self, patent_df: pd.DataFrame, corp_info_df: pd.DataFrame, top_k: int) -> list:
        """데이터를 병합하고 상위 k개의 데이터를 가져온다.
        Args:
            patent_df: 유사한 특허의 기업 데이터
            corp_info_df: 법인 번호에 따른 기업 정보
            top_k: 상위 몇개의 기업 정보를 가져올지
        Returns:
            result: 유사한 특허를 가진 기업 정보, 관리자 정보, 평균 유사도, 특허 개수
        """
        final_df = pd.merge(patent_df, corp_info_df, left_on="corp_num", right_on="corporation_num")
        final_df["avg_score"] = final_df.groupby("corp_num")["avg_score"].transform("mean")
        return final_df.head(top_k).to_dict("records")

    def get_corp_with_similar_patent(self, applicate_number: str, top_k: int) -> dict:
        """출원번호에 해당하는 특허와 유사한 특허를 가진 기업 정보와 관리자 정보, 유사도를 가져온다.
        Args:
            applicate_number: 특허 출원번호
            top_k: 상위 몇개의 기업 정보를 가져올지 (평균 유사도 기준)
        Returns:

        """
        result_cnt = 0
        total_cnt = 0
        response = {
            "status": "fail",
            "code": 666,
            "message": "특허 정보 조회에 실패했습니다.",
            "data": {"results": []},
        }

        with cpu_engine.connect() as cpu_conn, dev_engine.connect() as dev_conn:
            try:
                # 유사한 특허 데이터 가져오기
                sim_df, total_cnt = self.fetch_similar_patents(applicate_number, cpu_conn)
                try:
                    sim_df = sim_df[sim_df["sim"] > SIMILARITY_THRESHOLD]
                except KeyError:  # sim column이 없는 경우: 출원번호로 조회된 특허가 없는 경우
                    response["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
                    response["message"] = (
                        format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
                        + NO_INFO_MSG
                    )
                    return response

                if sim_df.empty:  # 유사한 특허가 없는 경우
                    response["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
                    response["message"] = (
                        format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
                        + NO_SIMILAR_PATENT_MSG
                    )
                    return response

                # 유사한 특허의 출원번호를 기반으로 기업 데이터(법인번호, 특허 출원번호) 가져오기
                patent_df = self.fetch_and_extract_patent_data(sim_df, cpu_conn)
                if patent_df.empty:  # 유사한 특허의 기업 데이터가 없는 경우
                    response["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
                    response["message"] = (
                        format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
                        + NO_CORP_INFO_MSG
                    )
                    return response
                patent_df = self.preprocess_patent_data(patent_df)

                # 법인 번호를 기반으로 기업 정보 가져오기
                corp_info_df = self.fetch_corp_info(patent_df, dev_conn)

                if corp_info_df.empty:
                    response["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
                    response["message"] = (
                        format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
                        + EMPTY_RESULT_MSG
                    )
                    return response

                # 데이터 병합 및 처리
                result = self.combine_data(patent_df, corp_info_df, top_k)
                result_cnt = len(result)
                del sim_df, patent_df, corp_info_df
                response["code"] = Success.SUCCESS["code"]
                response["message"] = (
                    Success.SUCCESS["message"]
                    + ": "
                    + OK_MSG.format(total_cnt, SIMILARITY_THRESHOLD, result_cnt)
                )
                response["data"]["results"] = result
                # data>results 안에 있는 key를 snake_case를 camelCase로 변환
                response["data"]["results"] = [
                    {snake_to_camel(key): value for key, value in result.items()}
                    for result in response["data"]["results"]
                ]
                response["status"] = "success"
            except Exception as e:
                response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
                response["message"] = GENERAL_ERROR_MSG.format(e)
                ic(traceback.format_exc())
        return response


if __name__ == "__main__":
    applicate_number = "1020230055574"
    top_k = 5
    patent_buyer_info = PatentBuyerInfoUtils()
    result = patent_buyer_info.get_corp_with_similar_patent(applicate_number, top_k)
    ic(result)
