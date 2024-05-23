import datetime as dt

PATENT_GEN_INST_PROMPT = """
---
Draft patent
---
##title
Please give a name for this invention.

##abstract
In this section, explain the following in sufficient detail for a layperson to understand.
If the written text is less than 500 words, add more content to fit within 500 words.
- Tone: Politely
- Style: Detailed and accurate
- detail :
   (summary contents)
   (Core technology features)
   (Problem you want to solve)
   (Excellence compared to existing technology)
   (Possibilities and advantages of the invention)

##target
In this section, explain the following in sufficient detail for a layperson to understand.
If the written text is less than 500 words, add more content to fit within 500 words.
- Tone: Politely
- Style: Detailed and accurate
- detail :
   (problem or limitation)
   (Detailed problem definition)
   (Expected results and effects)

##method
In this section, explain the following in sufficient detail for a layperson to understand.
If the written text is less than 500 words, add more content to fit within 500 words.
- Tone: Politely
- Style: Detailed and accurate
- detail :
   (Problem mentioned in problem definition)
   (Key procedures and technical details of the solution)
   (Innovative features compared to existing methods)
   (Technical features that provide superiority of the solution)

##effect
In this section, explain the following in sufficient detail for a layperson to understand.
If the written text is less than 500 words, add more content to fit within 500 words.
- Tone: Politely
- Style: Detailed and accurate
- detail :
   (Innovativeness compared to existing technology)
   (Features of the solution)
   (Unique feature compared to other methods)
   (Special Benefits and Effects)

##tech
In this section, explain the following in sufficient detail for a layperson to understand.
If the written text is less than 500 words, add more content to fit within 500 words.
- Tone: Politely
- Style: Detailed and accurate
- detail :
   (Technical field related to the problem you are trying to solve)
   (Main technical features of the solution)
   (Innovativeness compared to existing technology)
   (Possibility of application and scope of application of the invention)

##ipc
Please list the closest IPC codes related to the technology in which this invention is expressed.
Duplicate codes are not permitted.

##prior_art
In this section, explain the following in sufficient detail for a layperson to understand.
If the written text is less than 500 words, add more content to fit within 500 words.
- Tone: Politely
- Style: Detailed and accurate
- detail :
   (Background technology related to the problem you are trying to solve)
   (past research or technology trends)
   (Basic knowledge essential for understanding the problem you are trying to solve)
   (Innovativeness and necessity of the invention)

Make the result like the one in the <example>~</example> section.
Write it in json format with each item as the key and the content as the value,
and deliver it as complete data with no errors in parsing as json.

---
Final result options
Format: json
---
<example>
{
   "title": "Content",
   "abstract": "content",
   "target": "content",
   "method": "content",
   "effect": "content",
   "tech": "content",
   "ipc": ["ipc_code1"],
   "prior_art": "Content"
}
</example>
And response is translate to korean
""".strip()

PATENT_META_FIELD_INFO = [
   {
      "name": "abstract",
      "description": "The content of the patent document. it was written in korean",
      "type": "String",
   },
   {
      "name": "applicate_date",
      "description": "The date of the patent application. That field format is 'YYYY-MM-DD' ",
      "type": "date",
   },
   {
      "name": "applicate_number",
      "description": ("The number of the patent application."
                      "it is unique and can be used as a primary key"),
      "type": "string",
   },
   {
      "name": "invention_title",
      "description": "The title of the invention. it was written in korean ",
      "type": "string",
   },
   {
      "name": "invention_eng_title",
      "description": "The title of the invention. it was written in english ",
      "type": "String",
   },
   {
      "name": "ipcs",
      "description": "related ipc codes.",
      "type": "String",
   },
   {
      "name": "keyword",
      "description": "keyword that can be represent of invention",
      "type": "String",
   },
   {
      "name": "lrh_name",
      "description": "The name of the invetion's owner or right holder",
      "type": "String",
   },
   {
      "name": "open_number",
      "description": ("When invention is opened, it has a number."
                      "it is unique and can be used as a primary key"),
      "type": "String",
   },
   {
      "name": "register_number",
      "description": ("When invention is registered, it has a number, else it was empty."
                      "it is unique and can be used as a primary key"),
      "type": "String",
   },
   {
      "name": "claim_text",
      "description": "The text of the claim, this mean the invention's right",
      "type": "String",
   },
]

PATENT_QUERY_FEW_SHOT_EXAMPLES = [
   (
      "최근 5년 이내 반도체 검사용 초음파 장치 관련 특허를 보여줘",
      {
         "query": "5년 이내,반도체 검사용 초음파 장치",
         "filter": 'and(gte("applicate_date","2021-02-28"),or(like("claim_text","반도체 검사용 초음파 장치"),'
         'like("invention_title","반도체 검사용 초음파 장치"),like("abstract","반도체 검사용 초음파 장치")))',
      },
   ),
   (
      "2010년도 이후 2차전지 관련 특허를 보여줘",
      {
         "query": "2차전지",
         "filter": 'and(gte("applicate_date","2010-01-01"),or(like("invention_title","2차전지"),'
         'like("claim_text","2차전지"),like("abstract","2차전지")))',
      },
   ),
   (
      "2015년에 나온 이종재료를 이용한 특허를 보여줘",
      {
         "query": "이종재료",
         "filter": 'and(gte("applicate_date","2015-01-01"),lte("applicate_date","2015-12-31"),or(like("invention_title","이종재료"),'
         'like("claim_text","이종재료"),like("abstract","이종재료")))',
      },
   ),
   (
      "2020년과 2023년에 나온 자전거 관련 특허를 검색해줘",
      {
         "query": "2020년과 2023년에 나온 자전거 관련 특허를 검색해줘",
         "filter": (
               'and(or(and(gte("applicate_date","2020-01-01"),lte("applicate_date","2020-12-31")),'
               'and(gte("applicate_date","2023-01-01"),lte("applicate_date","2023-12-31")),'
               'or(like("claim_text","자전거"),like("invention_title","자전거"),like("abstract","자전거")))'
         ),
      },
   ),
   (
      "2023년 상반기에 출원된 반도체 관련 특허를 보여줘",
      {
         "query": "반도체",
         "filter": 'and(gte("applicate_date","2023-01-01"),lte("applicate_date","2023-06-30"),or(like("invention_title","반도체"),'
         'like("claim_text","반도체"),like("abstract","반도체")))',
      },
   ),
   (
      "2024년 1~3월 사이에 출원된 스마트폰 관련 특허를 찾아줘",
      {
         "query": "스마트폰",
         "filter": 'and(gte("applicate_date","2024-01-01"),lte("applicate_date","2024-03-31"),or(like("invention_title","스마트폰"),'
         'like("claim_text","스마트폰"),like("abstract","스마트폰")))',
      },
   ),
   (
      "2차전지와 생산 시스템이라는 키워드가 포함된 최근 5년 이내의 특허를 보여줘",
      {
         "query": "2차전지 생산 시스템",
         "filter": (
            'and(gte("applicate_date","2021-02-28"),'
            'or(like("invention_title","2차전지 생산 시스템"),'
            'like("claim_text","2차전지 생산 시스템"),'
            'like("abstract","2차전지 생산 시스템")))'
         ),
      },
   ),
   (
      "연속적인 톱니 플랭크 관련된 권리자가 삼성전자주식회사인 최근 5년 이내의 특허를 보여줘 특허를 보여줘",
      {
         "query": "연속적인 톱니 플랭크,삼성전자주식회사",
         "filter": (
            'and(gte("applicate_date","2021-02-28"),'
            'or(like("lrh_name","삼성전자주식회사"),'
            'like("invention_title","연속적인 톱니 플랭크"),'
            'like("claim_text","연속적인 톱니 플랭크"),'
            'like("abstract","연속적인 톱니 플랭크")))'
         ),
      },
   ),
   (
      ("뚜껑을 선회시켜 점화하는 라이타에 관한 발명으로, 본체 내부에 가스통과 점화를 위한 압전장치를 구비,"
       "뚜껑을 피봇축을 중심으로 선회시켜 점화된다. 회전식 뚜껑으로 다양한 디자인이 가능하다. 이러한 발명에 대한 특허를 보여줘"),
      {
         "query": "뚜껑 선회 라이타",
         "filter": 'and(or(like("invention_title","뚜껑 선회 라이타"),like("claim_text","뚜껑 선회 라이타"),'
         'like("abstract","뚜껑 선회 라이타")))',
      },
   ),
   (
      "특정한 약물을 이용한 암 치료 방법에 대한 발명으로, 약물을 투여하여 암 세포의 증식을 억제하고 종양을 축소시킨다. 이러한 발명에 대한 특허를 보여줘",
      {
         "query": "암 치료 방법",
         "filter": (
            'or(like("invention_title","암 치료 방법"),'
            'like("claim_text","암 치료 방법"),'
            'like("abstract","암 치료 방법"))'
         ),
      },
   ),
   (
      "플라스틱 재료를 이용한 친환경 제품에 관한 발명으로, 플라스틱 재료를 재활용하여 다양한 제품을 생산한다. 이러한 발명에 대한 특허를 보여줘",
      {
         "query": "친환경 제품",
         "filter": (
            'or(like("invention_title","친환경 제품"),'
            'like("claim_text","친환경 제품"),'
            'like("abstract","친환경 제품"))'
         ),
      },
   ),
   (
      "인공지능을 이용한 자율주행 자동차에 관한 발명으로, 인공지능 알고리즘을 적용하여 자동차가 스스로 주행할 수 있다. 이러한 발명에 대한 특허를 보여줘",
      {
         "query": "자율주행 자동차",
         "filter": (
            'or(like("invention_title","자율주행 자동차"),'
            'like("claim_text","자율주행 자동차"),'
            'like("abstract","자율주행 자동차"))'
         ),
      },
   ),
   (
      "태양광 발전 시스템에 관한 발명으로, 태양광 패널을 이용하여 전기를 생산한다. 이러한 발명에 대한 특허를 보여줘",
      {
         "query": "태양광 발전 시스템",
         "filter": (
            'or(like("invention_title","태양광 발전 시스템"),'
            'like("claim_text","태양광 발전 시스템"),'
            'like("abstract","태양광 발전 시스템"))'
         ),
      },
   ),
]

PATENT_DOC_CONTENT_DESC = f"""
The content of the patent document. it was written in korean
When converting to specific dates, use current date is {dt.datetime.now().date()} as the reference
and adjust it to match the Korean Standard Time (KST) timezone.
"""
