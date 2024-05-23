import re
import os
import ast
import random
import typing as t

import torch
import numpy as np
from datasets import logging


logging.set_verbosity(logging.ERROR)


def convert_format(input_datas: t.Dict, model_name: t.Text):
    """
    데이터 처리를 위해 id와 content를 분리하는 함수

    input : input_datas, model_name

    output : id_dict, content_dict, extra_list

    """
    id_list, content_list, extra_list = [], [], []
    id_dict, content_dict = {}, {}
    for input_data in input_datas:
        input_data["content"] = processing(input_data["content"])
        print("input_data : ", input_data["content"])
        if not "\n\n".join(input_data["content"]):
            extra_list.append({"id": input_data["id"], "label": ""})
            continue
        id_list.append(input_data["id"])
        if "investment" in model_name:
            instruct_text = "title: {}\ncontent: {}".format(
                text_normalize(input_data["title"]),
                text_normalize("".join(input_data["content"])),
            )
            # print("instruct_text : ", instruct_text)
            content_list.append(instruct_text)
        else:
            content_list.append(input_data["content"])

    id_dict["id"] = id_list
    content_dict["content"] = content_list
    return id_dict, content_dict, extra_list


def seed_everything(seed):
    """
    재현성을 위한 시드 설정 함수

    input : seed

    """
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)


def processing(content: t.Text) -> t.Text:
    result = str(content)
    pattern = [
        re.compile("\(\d{6}\)"),  # 기업 종목 코드 (6자리)
        re.compile(
            r"\(?[-_0-9a-z]+@[-_0-9a-z]+(?:\.[0-9a-z]+)+\)?", flags=re.IGNORECASE
        ),  # 이메일 주소
        re.compile(
            "\[?[가-힣]{1,8} [가-힣]+ ?기자\]?|[가-힣]+ ?신문|[가-힣]+투데이|[가-힣]+미디어|[가-힣]+ ?데일리|[가-힣]+ 콘텐츠 무단|[가-힣]+ ?전재|[가-힣]+배포 ?금지"
        ),  # 기자 이름, 미디어 명칭,배포 금지
        re.compile(
            r"\.([^\.]*(?:기자|특파원|교수|작가|대표|논설|고문|주필|부문장|팀장|장관|원장|연구원|이사장|위원|실장|차장|부장|에세이|화백|사설|소장|단장|과장|기획자|큐레이터|저작권|평론가|©|©|ⓒ|\@|\/|=|▶|무단|전재|재배포|금지|\[|\]|\(\))[^\.]*)$"
        ),  # 특정 단어로 끝나는 문장
        re.compile("[\r|\n]"),  # 개행문자
        re.compile(
            r"(?:https?:\/\/)+[-_0-9a-z]+(?:\.[-_0-9a-z]+)+|웹사이트", flags=re.IGNORECASE
        ),  # URL 주소
        re.compile(
            "[^\w\s,.%‘’~&+]"
        ),  # 한글,영어,숫자,공백,콤마,점,퍼센트,따옴표,~,&를 제외한 모든 문자
    ]
    for idx, ptn in enumerate(pattern):
        result = ptn.sub("" if idx == 0 or idx == 3 else " ", result)

    return result.strip()


def esg_company_dumps(data: t.List[t.Text]) -> t.List[t.Text]:
    """
    ESG 감정분석 결과를 딕셔너리 형태로 변환하는 함수

    input : ESG 감정분석 결과

    output : ESG 감정분석 결과 딕셔너리
    """
    data = "".join(data)
    if "\\n" not in data:
        data.split(".")[:-1]
    data_list = data.split("\\n")
    # 결과를 저장할 딕셔너리 생성
    result = {}
    # 각 줄을 반복하면서 정보를 추출
    for line in data_list:
        if line.lower() == "none":
            pass
        try:
            match = re.match(
                r"(.+?)의 (.+?)는 (.+?)은 (\d+)%, (.+?)은 (\d+)%, (.+?)은 (\d+)% 이다",
                line,
            )
            if not match:
                match = re.match(
                    r"(.+?)의 (.+?)는 (.+?)은 (\d+), (.+?)은 (\d+), (.+?)은 (\d+) 이다",
                    line,
                )
            if match:
                company = match.group(1)  # 회사 이름 추출
                sentiment_type = match.group(2)  # 감정 카테고리 추출
                positive = match.group(3)  # 긍정 극성
                positive_idx = match.group(4)  # 긍정 극성
                negative = match.group(5)  # 부정 극성
                negative_idx = match.group(6)  # 부정 극성
                neutral = match.group(7)  # 중립 극성
                neutral_idx = match.group(8)  # 중립 극성

                # 결과 딕셔너리에 정보 추가
                if company not in result:
                    result[company] = {}
                if sentiment_type not in result[company]:
                    result[company][sentiment_type] = {
                        positive: int(positive_idx),
                        negative: int(negative_idx),
                        neutral: int(neutral_idx),
                    }
        except Exception as e:
            print("Error 발생 : ", e)
    result = list(result.keys())
    return result


def esg_dumps(data: t.Text) -> t.Dict[t.Text, t.Dict[t.Text, t.Dict[t.Text, int]]]:
    """
    ESG 감정분석 결과를 딕셔너리 형태로 변환하는 함수

    input : ESG 감정분석 결과

    output : ESG 감정분석 결과 딕셔너리
    """

    if "\\n" not in data:
        data.split(".")[:-1]
    data_list = data.split("\\n")
    # 결과를 저장할 딕셔너리 생성
    result = {}
    # 각 줄을 반복하면서 정보를 추출
    for line in data_list:
        if line.lower() == "none":
            pass
        try:
            match = re.match(
                r"(.+?)의 (.+?)는 (.+?)은 (\d+)%, (.+?)은 (\d+)%, (.+?)은 (\d+)% 이다",
                line,
            )
            if not match:
                match = re.match(
                    r"(.+?)의 (.+?)는 (.+?)은 (\d+), (.+?)은 (\d+), (.+?)은 (\d+) 이다",
                    line,
                )
            if match:
                company = match.group(1)  # 회사 이름 추출
                sentiment_type = match.group(2)  # 감정 카테고리 추출
                positive = "positive"  # 긍정 극성
                positive_idx = match.group(4)  # 긍정 극성
                negative = "negative"  # 부정 극성
                negative_idx = match.group(6)  # 부정 극성
                neutral = "neutral"  # 중립 극성
                neutral_idx = match.group(8)  # 중립 극성

                # 결과 딕셔너리에 정보 추가
                if company not in result:
                    result[company] = {}
                if sentiment_type not in result[company]:
                    result[company][sentiment_type] = {
                        positive: int(positive_idx),
                        negative: int(negative_idx),
                        neutral: int(neutral_idx),
                    }
        except Exception as e:
            print("Error 발생 : ", e)

    return result


def category_dumps(data: t.List[str]) -> t.List[str]:
    """
    카테고리 분류 결과를 리스트 형태로 변환하는 함수

    input : 카테고리 분류 결과

    output : 카테고리 분류 결과 리스트
    """
    data = "".join(data)
    category_list = []
    try:
        # 뉴스 컨텐츠 또는 모델 생성 오류로 20개 이상 string을
        # 뽑아낼 경우 etc 반환
        if len(data) > 20:
            category_list.append("etc")
        else:
            data_list = data.split(",")
            for element in data_list:
                category_list.append(element)
    except Exception as e:
        print(f"에러 발생 {e}")

    return category_list


def keyphrase_dumps(data: t.List[str]) -> t.List[str]:
    """
    키워드 추출 결과를 리스트 형태로 변환하는 함수

    input : 키워드 추출 결과

    output : 키워드 추출 결과 리스트
    """
    data = "".join(data)
    keyphrase_list = []
    try:
        if "keyphrases" in data.lower():
            pass
        else:
            data_list = data.split(";")
            for elements in data_list:
                element = elements.strip()
                keyphrase_list.append(element)

    except Exception as e:
        print("Error 발생 \n", e)

    return list(set(keyphrase_list))


# 오류 발생으로 esg로 대체 중 24/05/02
# def company_dumps(data: t.List[str]) -> t.List[str]:
#     """
#     기업명과 감정분석이 쌍으로 된 결과를 파싱하는 함수

#     input : 기업명과 감정분석이 쌍으로 된 결과

#     output : 기업명 리스트
#     """

#     data = "".join(data)
#     company_list = []
#     try:
#         if "none" in data.lower():
#             pass
#         element = ast.literal_eval(data)
#         if element:
#             company_list += list(element.keys())

#     except SyntaxError as syn_error:
#         print(f"Syntax Error 발생 {syn_error}")

#     return company_list


def text_normalize(text: t.Text) -> t.Text:
    """
    텍스트 정규화 함수
    
    input : 뉴스 title 또는 content

    output : 정규화된 title 또는 content
    """
    p = re.compile(r"([\n ])\1+")   # 연속된 공백 제거

    return p.sub(r"\1", text.replace("\xa0", " "))  # \xa0 제거


def postprocess_keyphrase(data: list):
    """
    키워드 추출 결과를 후처리하는 함수
    
    input : 키워드 추출 결과
    
    output : 후처리된 키워드 추출 결과
    """
    result = []
    for keyword in data:
        if ',' in keyword:
            keyword = keyword.replace(',', '')  # 콤마 제거 (e.g. '삼성전자, 주가' -> '삼성전자 주가')
        result.append(keyword)
    return result
