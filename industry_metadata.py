from __future__ import annotations

INDUSTRIES = [
    {
        'suffix': '01',
        'employment_code': 'A040601',
        'non_private_wage_code': 'A040I01',
        'private_wage_code': 'A040M01',
        'name': '总计',
        'name_en': 'Total Urban Units',
        'category': 'all',
        'is_aggregate': True,
    },
    {
        'suffix': '02',
        'employment_code': 'A040602',
        'non_private_wage_code': 'A040I02',
        'private_wage_code': 'A040M02',
        'name': '农林牧渔业',
        'name_en': 'Agriculture, Forestry, Animal Husbandry and Fishery',
        'category': 'primary',
        'is_aggregate': False,
    },
    {
        'suffix': '03',
        'employment_code': 'A040603',
        'non_private_wage_code': 'A040I03',
        'private_wage_code': 'A040M03',
        'name': '采矿业',
        'name_en': 'Mining',
        'category': 'secondary',
        'is_aggregate': False,
    },
    {
        'suffix': '04',
        'employment_code': 'A040604',
        'non_private_wage_code': 'A040I04',
        'private_wage_code': 'A040M04',
        'name': '制造业',
        'name_en': 'Manufacturing',
        'category': 'secondary',
        'is_aggregate': False,
    },
    {
        'suffix': '05',
        'employment_code': 'A040605',
        'non_private_wage_code': 'A040I05',
        'private_wage_code': 'A040M05',
        'name': '电力、热力、燃气及水生产和供应业',
        'name_en': 'Utilities',
        'category': 'secondary',
        'is_aggregate': False,
    },
    {
        'suffix': '06',
        'employment_code': 'A040606',
        'non_private_wage_code': 'A040I06',
        'private_wage_code': 'A040M06',
        'name': '建筑业',
        'name_en': 'Construction',
        'category': 'secondary',
        'is_aggregate': False,
    },
    {
        'suffix': '07',
        'employment_code': 'A040607',
        'non_private_wage_code': 'A040I07',
        'private_wage_code': 'A040M07',
        'name': '交通运输、仓储和邮政业',
        'name_en': 'Transportation, Warehousing and Postal Services',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '08',
        'employment_code': 'A040608',
        'non_private_wage_code': 'A040I08',
        'private_wage_code': 'A040M08',
        'name': '信息传输、软件和信息技术服务业',
        'name_en': 'Information Transmission, Software and IT Services',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '09',
        'employment_code': 'A040609',
        'non_private_wage_code': 'A040I09',
        'private_wage_code': 'A040M09',
        'name': '批发和零售业',
        'name_en': 'Wholesale and Retail Trade',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0A',
        'employment_code': 'A04060A',
        'non_private_wage_code': 'A040I0A',
        'private_wage_code': 'A040M0A',
        'name': '住宿和餐饮业',
        'name_en': 'Accommodation and Food Services',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0B',
        'employment_code': 'A04060B',
        'non_private_wage_code': 'A040I0B',
        'private_wage_code': 'A040M0B',
        'name': '金融业',
        'name_en': 'Finance',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0C',
        'employment_code': 'A04060C',
        'non_private_wage_code': 'A040I0C',
        'private_wage_code': 'A040M0C',
        'name': '房地产业',
        'name_en': 'Real Estate',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0D',
        'employment_code': 'A04060D',
        'non_private_wage_code': 'A040I0D',
        'private_wage_code': 'A040M0D',
        'name': '租赁和商务服务业',
        'name_en': 'Leasing and Business Services',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0E',
        'employment_code': 'A04060E',
        'non_private_wage_code': 'A040I0E',
        'private_wage_code': 'A040M0E',
        'name': '科学研究和技术服务业',
        'name_en': 'Scientific Research and Technical Services',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0F',
        'employment_code': 'A04060F',
        'non_private_wage_code': 'A040I0F',
        'private_wage_code': 'A040M0F',
        'name': '水利、环境和公共设施管理业',
        'name_en': 'Water Conservancy, Environment and Public Facilities Management',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0G',
        'employment_code': 'A04060G',
        'non_private_wage_code': 'A040I0G',
        'private_wage_code': 'A040M0G',
        'name': '居民服务、修理和其他服务业',
        'name_en': 'Resident Services, Repairs and Other Services',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0H',
        'employment_code': 'A04060H',
        'non_private_wage_code': 'A040I0H',
        'private_wage_code': 'A040M0H',
        'name': '教育业',
        'name_en': 'Education',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0I',
        'employment_code': 'A04060I',
        'non_private_wage_code': 'A040I0I',
        'private_wage_code': 'A040M0I',
        'name': '卫生和社会工作',
        'name_en': 'Health and Social Work',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0J',
        'employment_code': 'A04060J',
        'non_private_wage_code': 'A040I0J',
        'private_wage_code': 'A040M0J',
        'name': '文化、体育和娱乐业',
        'name_en': 'Culture, Sports and Entertainment',
        'category': 'tertiary',
        'is_aggregate': False,
    },
    {
        'suffix': '0K',
        'employment_code': 'A04060K',
        'non_private_wage_code': 'A040I0K',
        'private_wage_code': 'A040M0K',
        'name': '公共管理、社会保障和社会组织',
        'name_en': 'Public Administration, Social Security and Social Organizations',
        'category': 'tertiary',
        'is_aggregate': False,
    },
]

INDUSTRY_BY_EMPLOYMENT_CODE = {
    industry['employment_code']: industry for industry in INDUSTRIES
}

INDUSTRY_BY_ANY_CODE = {}
for industry in INDUSTRIES:
    INDUSTRY_BY_ANY_CODE[industry['employment_code']] = industry
    INDUSTRY_BY_ANY_CODE[industry['non_private_wage_code']] = industry
    INDUSTRY_BY_ANY_CODE[industry['private_wage_code']] = industry

EMPLOYMENT_CODES = [industry['employment_code'] for industry in INDUSTRIES]
NON_PRIVATE_WAGE_CODES = [industry['non_private_wage_code'] for industry in INDUSTRIES]
PRIVATE_WAGE_CODES = [industry['private_wage_code'] for industry in INDUSTRIES]


def clean_indicator_name(name: str) -> str:
    cleaned = name.strip()
    replacements = [
        '城镇非私营单位就业人员平均工资',
        '按行业分城镇私营单位就业人员平均工资',
        '城镇私营单位就业人员平均工资',
        '城镇非私营单位就业人员',
        '按行业分',
        '平均工资',
        '_',
    ]
    for marker in replacements:
        cleaned = cleaned.replace(marker, '')
    return cleaned.strip(' -')


def get_industry(indicator_code: str):
    return INDUSTRY_BY_ANY_CODE.get(indicator_code)
