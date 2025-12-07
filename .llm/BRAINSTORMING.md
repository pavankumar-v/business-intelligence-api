# Steps to calculate daily metrics:

### what doe we need from daily metrics?

date + region wise - on this date and in this region what was the aggregated usage

total_cost
top_used_model
least_user_model
total_conversations

1. Group by date + region

```
2. output - {
    "2024-01-02EU": [
        {
            user_id: "342"
            conversation_id: "SDfsd",
            total_cost: 0.2,
            model: "claude"
        },
        {
            user_id: "2342"
            conversation_id: "SDfsd",
            total_cost: 0.6,
            model: "mistral"
        },
    ],
    "2024-01-02JP": [
        {
            user_id: "345345"
            conversation_id: "dfgd",
            total_cost: 1,
            model: "gpt"
        },
        {
            user_id: "23426"
            conversation_id: "sdahj",
            total_cost: 10,
            model: "claude"
        },
    ],
}
```

3. Group by date + region and SQL Query SUM(total_cost), SUM(convesation_id), SUM(Model)

```
4. output -
    [
        "2024-01-02EU": {
            "total_cost": 100,
            "total_conversations": 200,
            "heighest_used_model": "claude",
            "least_used_model": "gpt-3.5-low"
        },
        "2024-01-02JP": {
            "total_cost": 100,
            "total_conversations": 200,
            "heighest_used_model": "claude",
            "least_used_model": "gpt-3.5-low"
        },
        "2024-01-03EU": {
            "total_cost": 100,
            "total_conversations": 200,
            "heighest_used_model": "claude",
            "least_used_model": "gpt-3.5-low"
        }
    ]
```

# Steps to calculate company metrics:

1. Group Transactions By Company Name, date, region

```
   output - {
    "(2024-01-02,EU, Tech Global)": [
            {
                "conversation_id": "123",
                "model_name": "gpt-4o",
                "calculated_cost": 1.0,
                "token_count": 100
            },
            {
                "conversation_id": "123",
                "model_name": "gpt-4o",
                "calculated_cost": 1.0,
                "token_count": 100
            }
        ],
        "(2024-01-02,EU, Tech Global)": [
            {
                "conversation_id": "123",
                "model_name": "gpt-4o",
                "calculated_cost": 1.0,
                "token_count": 100
            }
        ]
   }
```

2. From SQL Query GROUP BY Company Name and for each group sum total_cost and conversation_id

```
   Final Result
   [
        {
            "company_name": "Tech Global",
            "date": "2024-01-02",
            "region": "EU",
            "total_cost": 200,
            "total_conversations": 100,
            "heighest_used_model": "gpt-4o",
            "least_used_model": "gpt-3.5-low"
        },
        {
            "company_name": "Tech Global2",
            "date": "2024-01-02",
            "region": "EU",
            "total_cost": 200,
            "total_conversations": 100,
            "heighest_used_model": "gpt-4o",
            "least_used_model": "gpt-3.5-low"
        }
   ]
```

# Steps to calculate daily model wise metrics:

1. Group Transactions By Model Name, Region and Date

```
   output - {
    "(2024-01-02, EU, gpt-o4)": [
        {
            "conversation_id": "123",
            "model_name": "gpt-4o",
            "calculated_cost": 1.0,
            "token_count": 100
        },
        {
            "conversation_id": "123",
            "model_name": "gpt-4o",
            "calculated_cost": 1.0,
            "token_count": 100
        }
    ]
   }
```

2. From SQL Query GROUP BY Model Name, Region and Date and for each group sum total_cost and conversation_id

```
   Final Result
   [
        {
            "model_name": "gpt-4o",
            "region": "EU",
            "date": "2024-01-02",
            "total_cost": 200,
            "conversation_count": 100,
        },
        {
            "model_name": "gpt-4o-mini",
            "region": "EU",
            "date": "2024-01-02",
            "total_cost": 100,
            "conversation_count": 50
        }
   ]
```
