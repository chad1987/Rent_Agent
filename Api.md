一、房源情况介绍
数据规模
    - 覆盖区域：北京行政区（如 海淀、朝阳、通州、昌平、大兴、房山、西城、丰台、顺义、东城）
    - 价格区间：约 500–25000 元/月
    - 支持查询：价格、户型、区域、地铁距离、附近地标、可入住日期、西二旗通勤时间等维度
    - 地标数据：地铁站、世界 500 强企业、商圈地标（含商超/公园）
数据源说明
1. 房源基础信息
覆盖地址、户型、面积、租金、可入住日期与楼层，可按行政区与商圈检索。
    - 地址：北京行政区，房源落在地铁站、商圈、世界 500 强企业所在地标周边，小区名与商圈具体名称由地标决定（例如西二旗、国贸、望京）。
    - 户型：整租与合租约各占 50%；整租为一居至四居多种室厅卫组合，面积约 22～145 ㎡；合租为单间，整套为 2 室、3 室或 4 室一厅一卫或两卫，单间面积约 12～30 ㎡，月租约 1200～3500 元。
    - 租金：整租月租约 800～28000 元/月，付款单位元/月。
2. 通勤信息
每条房源均带地铁与到西二旗通勤信息，支持按商圈、地铁距离、通勤时间筛选。
    - 最近地铁站及距地铁站距离约 200～5500 米分段覆盖。
    - 到西二旗通勤时间约 8～95 分钟。
3. 配置信息
仅覆盖周边生活配套中的商超与公园。
    - 可查房源周边商超、公园及距离。
4. 房屋设施
含电梯、装修、朝向、卫生间（室厅卫中的几卫），。
    - 装修：简装、精装、豪华、毛坯、空房。
    - 朝向：朝南、朝北、朝东、朝西、南北、东西。
    - 卫生间：以室、厅、卫中的「几卫」体现（如一卫、双卫）。
5. 房源隐形信息
含噪音水平、标签与房源状态，用于表达「近地铁但临街略吵」、采光等潜在信息。
    - 噪音水平：安静、中等、吵闹、临街。
    - 标签：近地铁、双地铁、多地铁；精装修、豪华装修、毛坯、空房；朝南、南北通透、采光好；有电梯、高楼层、高层；小户型、大户型、大两居、大三居、双卫；核心区、学区房、近高校；合租、小单间、商住；低价、高性价比、农村房、农村自建房；部分商圈或路名。
    - 房源状态：可租、已租、下架（约 90%、5%、5%）。

二、使用接口的硬性要求

请求头
房源相关接口（/api/houses/*）必须带请求头 X-User-ID，否则返回 400
地标接口（/api/landmarks/*）不需 X-User-ID。
X-User-ID的值即为用户工号，注意必须传比赛平台注册的用户工号，比赛的用例会按照用户工号隔离，若传值有误用例执行结果会有冲突影响成绩！


房源数据重置
用例执行过程中会改变房租的状态（可租/已租/下架），重复执行同一个用例时，由于数据状态发生改变会导致执行失败，因此建议在agent中定义每新起一个session，就去调用房源数据重置接口，保障每次用例执行都能够使用初始化的数据。

房源数据重置接口
调用示例：curl -s -X POST -H "X-User-ID: 真实工号" "http://7.225.29.223:8080/api/houses/init"
成功示例：{"code":0,"message":"success","data":{"action":"reset_user","message":"该用户状态覆盖已清空，房源恢复为初始状态","user_id":"真实工号"}}


注：自动判题 在每个用例执行前会自动进行房源数据初始化

租房/退租/下架操作
必须调用 对应API 才算完成操作，仅对话中生成 [已租] 无效

近距离概念说明
    - 近地铁：指房源到最近地铁站的直线距离。接口返回字段为 subway_distance（单位：米）。筛选时用参数 max_subway_dist：800 米以内视为近地铁，1000 米以内视为地铁可达。
    - 地标附近房源（接口 9）：以地标为圆心，按直线距离（米）筛选，参数 max_distance 默认 2000。返回结果中同时给出 distance_to_landmark（直线距离）、walking_distance（估算步行距离）、walking_duration（估算步行时间，分钟）。
    - 小区周边地标（接口 10）：以该小区为基准点，按直线距离（米）筛选，参数 max_distance_m 默认 3000，用于查商超、公园等周边配套。



三、可用接口列表

服务：http://7.225.29.223:8080

    | 序号                                                                                                                                                    | 方法 | 路径                             | 描述                                                                                                                                                                                               |
    |---------------------------------------------------------------------------------------------------------------------------------------------------------|------|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | 1                                                                                                                                                       | GET  | /api/landmarks                   | 获取地标列表，支持 category、district 同时筛选（取交集）。用于查地铁站、公司、商圈等地标。不需 X-User-ID。                                                                                         |
    | 2                                                                                                                                                       | GET  | /api/landmarks/name/{name}       | 按名称精确查询地标，如西二旗站、百度。返回地标 id、经纬度等，用于后续 nearby 查房。不需 X-User-ID。                                                                                                |
    | 3                                                                                                                                                       | GET  | /api/landmarks/search            | 关键词模糊搜索地标，q 必填。支持 category、district 同时筛选，多条件取交集。不需 X-User-ID。                                                                                                       |
    | 4                                                                                                                                                       | GET  | /api/landmarks/{id}              | 按地标 id 查询地标详情。不需 X-User-ID。                                                                                                                                                           |
    | 5                                                                                                                                                       | GET  | /api/landmarks/stats             | 获取地标统计信息（总数、按类别分布等）。不需 X-User-ID。                                                                                                                                           |
    | 6                                                                                                                                                       | GET  | /api/houses/{house_id}           | 根据房源 ID 获取单套房源详情。无 query 参数，仅路径带 house_id，返回一条（安居客），便于智能体解析。调用时请求头必带 X-User-ID。
    | 7                                                                                                                                                       | GET  | /api/houses/listings/{house_id}
    | 根据房源 ID 获取该房源在链家/安居客/58同城等各平台的全部挂牌记录。无 query 参数。调用时请求头必带 X-User-ID。响应 data 为 { total, page_size, items }。
    | 8                                                                                                                                                       | GET  | /api/houses/by_community         | 按小区名查询该小区下可租房源。默认每页 10 条、未传 listing_platform 时只返回安居客。用于指代消解、查某小区地铁信息或隐性属性。调用时请求头必带 X-User-ID。                                         |
    | 9                                                                                                                                                       | GET  | /api/houses/by_platform          | 查询可租房源，支持按挂牌平台筛选。listing_platform 可选：不传则默认使用安居客；传 链家/安居客/58同城 则只返回该平台。其他参数同 GET /api/houses。调用时请求头必带 X-User-ID。                      |
    | 10                                                                                                                                                      | GET  | /api/houses/nearby               | 以地标为圆心，查询在指定距离内的可租房源，返回带直线距离、步行距离、步行时间。默认每页 10 条、未传 listing_platform 时只返回安居客。需先通过地标接口获得 landmark_id。调用时请求头必带 X-User-ID。 |
    | 11                                                                                                                                                      | GET  | /api/houses/nearby_landmarks     | 查询某小区周边某类地标（商超/公园），按距离排序。用于回答「附近有没有商场/公园」。调用时请求头必带 X-User-ID。                                                                                     |
    | 12                                                                                                                                                      | GET  | /api/houses/stats                | 获取房源统计信息（总套数、按状态/行政区/户型分布、价格区间等），按当前用户视角统计。调用时请求头必带 X-User-ID。                                                                                   |
    | 13                                                                                                                                                      | POST | /api/houses/{house_id}/rent      | 将当前用户视角下该房源设为已租。传入房源 ID 与 listing_platform（必填，链家/安居客/58同城）以明确租赁哪个平台；三平台状态一并更新，响应返回该条。调用时请求头必带 X-User-ID。                      |
    | 14                                                                                                                                                      | POST | /api/houses/{house_id}/terminate | 将当前用户视角下该房源恢复为可租。传入房源 ID 与 listing_platform（必填）以明确操作哪个平台；三平台状态一并更新，响应返回该条。调用时请求头必带 X-User-ID。                                        |
    | 15                                                                                                                                                      | POST | /api/houses/{house_id}/offline   | 将当前用户视角下该房源设为下架。传入房源 ID 与 listing_platform（必填）以明确操作哪个平台；三平台状态一并更新，响应返回该条。调用时请求头必带 X-User-ID。                                          |

FAQ
Q：重复执行同一个用例，第二次执行后房源数据查询不到了
A：首次执行用例时，将房源数据状态更新为了已租，再次执行用例查询可租房源时返回结果必然为空。此时可以手动触发房源重置接口（见章节3）

接口实现详情如下：
{
    "openapi": "3.0.3",
    "info": {
        "title": "Fake App Agent API",
        "version": "1.0.0",
        "description": "租房仿真与评测用 API，地标与房源查询、租房/退租/下架等"
    },
    "servers": [
        {
            "url": "http://7.225.29.223:8080",
            "description": "租房仿真服务"
        }
    ],
    "paths": {
        "/api/landmarks": {
            "get": {
                "operationId": "get_landmarks",
                "summary": "获取地标列表",
                "description": "获取地标列表，支持 category、district 同时筛选（取交集）。用于查地铁站、公司、商圈等地标。不需 X-User-ID。",
                "parameters": [
                    {
                        "name": "category",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "地标类别：subway(地铁)/company(公司)/landmark(商圈等)，不传则不过滤"
                        }
                    },
                    {
                        "name": "district",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "行政区，如 海淀、朝阳"
                        }
                    }
                ]
            }
        },
        "/api/landmarks/name/{name}": {
            "get": {
                "operationId": "get_landmark_by_name",
                "summary": "按名称精确查询地标",
                "description": "按名称精确查询地标，如西二旗站、百度。返回地标 id、经纬度等，用于后续 nearby 查房。不需 X-User-ID。",
                "parameters": [
                    {
                        "name": "name",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "地标名称，如 西二旗站、国贸"
                        }
                    }
                ]
            }
        },
        "/api/landmarks/search": {
            "get": {
                "operationId": "search_landmarks",
                "summary": "关键词模糊搜索地标",
                "description": "关键词模糊搜索地标，q即地标名比如西二旗。支持 category、district 同时筛选，多条件取交集。不需 X-User-ID。",
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "搜索关键词，必填"
                        }
                    },
                    {
                        "name": "category",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "可选，限定类别：subway/company/landmark"
                        }
                    },
                    {
                        "name": "district",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "可选，限定行政区，如 海淀、朝阳"
                        }
                    }
                ]
            }
        },
        "/api/landmarks/{id}": {
            "get": {
                "operationId": "get_landmark_by_id",
                "summary": "按地标 id 查询地标详情",
                "description": "按地标 id 查询地标详情。不需 X-User-ID。",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "地标 ID，如 SS_001、LM_002"
                        }
                    }
                ]
            }
        },
        "/api/landmarks/stats": {
            "get": {
                "operationId": "get_landmark_stats",
                "summary": "获取地标统计信息",
                "description": "获取地标统计信息（总数、按类别分布等）。不需 X-User-ID。",
                "parameters": []
            }
        },
        "/api/houses/{house_id}": {
            "get": {
                "operationId": "get_house_by_id",
                "summary": "根据房源 ID 获取详情",
                "description": "根据房源 ID 获取单套房源详情。无 query 参数，仅路径带 house_id，返回一条（安居客），便于智能体解析。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "house_id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "房源 ID，如 HF_2001"
                        }
                    }
                ]
            }
        },
        "/api/houses/listings/{house_id}": {
            "get": {
                "operationId": "get_house_listings",
                "summary": "根据房源 ID 获取各平台挂牌记录",
                "description": "根据房源 ID 获取该房源在链家/安居客/58同城等各平台的全部挂牌记录。无 query 参数。调用时请求头必带 X-User-ID。响应 data 为 { total, page_size, items }。",
                "parameters": [
                    {
                        "name": "house_id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "房源 ID，如 HF_2001"
                        }
                    }
                ]
            }
        },
        "/api/houses/by_community": {
            "get": {
                "operationId": "get_houses_by_community",
                "summary": "按小区名查询可租房源",
                "description": "按小区名查询该小区下可租房源。默认每页 10 条、未传 listing_platform 时只返回安居客。用于指代消解、查某小区地铁信息或隐性属性。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "community",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "小区名，与数据一致，如 建清园(南区)、保利锦上(二期)"
                        }
                    },
                    {
                        "name": "listing_platform",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "链家",
                                "安居客",
                                "58同城"
                            ],
                            "description": "挂牌平台，不传则默认安居客"
                        }
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "页码，默认 1"
                        }
                    },
                    {
                        "name": "page_size",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "每页条数，默认 10，最大 10000"
                        }
                    }
                ]
            }
        },
        "/api/houses/by_platform": {
            "get": {
                "operationId": "get_houses_by_platform",
                "summary": "按挂牌平台筛选房源（平台可选）",
                "description": "查询可租房源，支持按挂牌平台筛选。listing_platform 可选：不传则默认使用安居客；传 链家/安居客/58同城 则只返回该平台。其他参数同 GET /api/houses。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "listing_platform",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "链家",
                                "安居客",
                                "58同城"
                            ],
                            "description": "挂牌平台，可选。不传则默认安居客；传则仅返回该平台"
                        }
                    },
                    {
                        "name": "district",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "行政区，逗号分隔，如 海淀,朝阳"
                        }
                    },
                    {
                        "name": "area",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "商圈，逗号分隔，如 西二旗,上地"
                        }
                    },
                    {
                        "name": "min_price",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "最低月租金（元）"
                        }
                    },
                    {
                        "name": "max_price",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "最高月租金（元）"
                        }
                    },
                    {
                        "name": "bedrooms",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "卧室数，逗号分隔，如 1,2"
                        }
                    },
                    {
                        "name": "rental_type",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "整租 或 合租"
                        }
                    },
                    {
                        "name": "decoration",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "精装/简装 等"
                        }
                    },
                    {
                        "name": "orientation",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "朝向，如 朝南、南北"
                        }
                    },
                    {
                        "name": "elevator",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "是否有电梯：true/false"
                        }
                    },
                    {
                        "name": "min_area",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "最小面积（平米）"
                        }
                    },
                    {
                        "name": "max_area",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "最大面积（平米）"
                        }
                    },
                    {
                        "name": "property_type",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "物业类型，如 住宅"
                        }
                    },
                    {
                        "name": "subway_line",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "地铁线路，如 13号线"
                        }
                    },
                    {
                        "name": "max_subway_dist",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "最大地铁距离（米），近地铁建议 800"
                        }
                    },
                    {
                        "name": "subway_station",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "地铁站名，如 车公庄站"
                        }
                    },
                    {
                        "name": "utilities_type",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "水电类型，如 民水民电"
                        }
                    },
                    {
                        "name": "available_from_before",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "可入住日期上限，YYYY-MM-DD（如 2026-03-10）"
                        }
                    },
                    {
                        "name": "commute_to_xierqi_max",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "到西二旗通勤时间上限（分钟）"
                        }
                    },
                    {
                        "name": "sort_by",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "排序字段：price/area/subway"
                        }
                    },
                    {
                        "name": "sort_order",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "asc 或 desc"
                        }
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "页码，默认 1"
                        }
                    },
                    {
                        "name": "page_size",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "每页条数，默认 10，最大 10000"
                        }
                    }
                ]
            }
        },
        "/api/houses/nearby_landmarks": {
            "get": {
                "operationId": "get_nearby_landmarks",
                "summary": "查询小区周边地标",
                "description": "查询某小区周边某类地标（商超/公园），按距离排序。用于回答「附近有没有商场/公园」。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "community",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "小区名，用于定位基准点"
                        }
                    },
                    {
                        "name": "type",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "description": "地标类型：shopping(商超) 或 park(公园)，不传则不过滤"
                        }
                    },
                    {
                        "name": "max_distance_m",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "number",
                            "description": "最大距离（米），默认 3000"
                        }
                    }
                ]
            }
        },
        "/api/houses/nearby": {
            "get": {
                "operationId": "get_houses_nearby",
                "summary": "以地标为圆心查附近房源",
                "description": "以地标为圆心，查询在指定距离内的可租房源，返回带直线距离、步行距离、步行时间。默认每页 10 条、未传 listing_platform 时只返回安居客。需先通过地标接口获得 landmark_id。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "landmark_id",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "地标 ID 或地标名称（支持按名称查找）"
                        }
                    },
                    {
                        "name": "max_distance",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "number",
                            "description": "最大直线距离（米），默认 2000"
                        }
                    },
                    {
                        "name": "listing_platform",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "链家",
                                "安居客",
                                "58同城"
                            ],
                            "description": "挂牌平台，不传则默认安居客"
                        }
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "页码，默认 1"
                        }
                    },
                    {
                        "name": "page_size",
                        "in": "query",
                        "required": false,
                        "schema": {
                            "type": "integer",
                            "description": "每页条数，默认 10，最大 10000"
                        }
                    }
                ]
            }
        },
        "/api/houses/stats": {
            "get": {
                "operationId": "get_house_stats",
                "summary": "获取房源统计信息",
                "description": "获取房源统计信息（总套数、按状态/行政区/户型分布、价格区间等），按当前用户视角统计。调用时请求头必带 X-User-ID。",
                "parameters": []
            }
        },
        "/api/houses/{house_id}/rent": {
            "post": {
                "operationId": "rent_house",
                "summary": "租房",
                "description": "将当前用户视角下该房源设为已租。传入房源 ID 与 listing_platform（必填，链家/安居客/58同城）以明确租赁哪个平台；三平台状态一并更新，响应返回该条。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "house_id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "房源 ID，如 HF_2001"
                        }
                    },
                    {
                        "name": "listing_platform",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "链家",
                                "安居客",
                                "58同城"
                            ],
                            "description": "必填。明确租赁哪个平台；三平台状态都会更新，返回该条"
                        }
                    }
                ]
            }
        },
        "/api/houses/{house_id}/terminate": {
            "post": {
                "operationId": "terminate_rental",
                "summary": "退租",
                "description": "将当前用户视角下该房源恢复为可租。传入房源 ID 与 listing_platform（必填）以明确操作哪个平台；三平台状态一并更新，响应返回该条。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "house_id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "房源 ID，如 HF_2001"
                        }
                    },
                    {
                        "name": "listing_platform",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "链家",
                                "安居客",
                                "58同城"
                            ],
                            "description": "必填。明确操作哪个平台；三平台状态都会更新，返回该条"
                        }
                    }
                ]
            }
        },
        "/api/houses/{house_id}/offline": {
            "post": {
                "operationId": "take_offline",
                "summary": "下架",
                "description": "将当前用户视角下该房源设为下架。传入房源 ID 与 listing_platform（必填）以明确操作哪个平台；三平台状态一并更新，响应返回该条。调用时请求头必带 X-User-ID。",
                "parameters": [
                    {
                        "name": "house_id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "description": "房源 ID，如 HF_2001"
                        }
                    },
                    {
                        "name": "listing_platform",
                        "in": "query",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "链家",
                                "安居客",
                                "58同城"
                            ],
                            "description": "必填。明确操作哪个平台；三平台状态都会更新，返回该条"
                        }
                    }
                ]
            }
        }
    }
}
