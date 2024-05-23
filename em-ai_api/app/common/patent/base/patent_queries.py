# 유사 특허 보유 기업 api 관련 쿼리 정의
patent_sim_query = """
SELECT patent, sim FROM
    (
    SELECT p1 AS patent, sim FROM patent_scraping.patent_sim WHERE p2 = :applicate_number
    UNION ALL
    SELECT p2 AS patent, sim FROM patent_scraping.patent_sim WHERE p1 = :applicate_number
    ) AS patent_sim
GROUP BY patent, sim
HAVING COUNT(*) = 1;
"""

patent_query = """
SELECT * FROM patent_scraping.corporation_patent_view
WHERE applicate_number = :applicate_number
;
"""

corp_info_query = """
SELECT
    nci.*,
    COALESCE(cm.manager_name, '') as manager_name,
    COALESCE(cm.position, '') as manager_position,
    COALESCE(cm.tel, '') as manager_tel,
    COALESCE(cm.email, '') as manager_email
FROM
    companies.new_company_info as nci
LEFT JOIN
    (SELECT biz_num, manager_name, position, tel, email
    FROM companies.company_manager_unique) cm
ON nci.biz_num = cm.biz_num
WHERE
    nci.corporation_num = :corporation_num
;
"""
