"""
Evaluation datasets and test case generators
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

def create_eval_dataset(dataset_type: str,
                       size: int = 10,
                       custom_cases: Optional[List[Dict]] = None) -> List[Dict[str, str]]:
    """
    Create evaluation dataset for testing

    Args:
        dataset_type: Type of dataset to create
        size: Number of test cases
        custom_cases: Custom test cases to include

    Returns:
        List of test cases with prompt/expected pairs
    """

    datasets = {
        "basic_qa": _create_basic_qa_dataset,
        "reasoning": _create_reasoning_dataset,
        "tool_usage": _create_tool_usage_dataset,
        "summarization": _create_summarization_dataset,
        "code_generation": _create_code_generation_dataset,
        "multi_language": _create_multi_language_dataset
    }

    if dataset_type not in datasets:
        raise ValueError(f"Unknown dataset type: {dataset_type}. Available: {list(datasets.keys())}")

    base_dataset = datasets[dataset_type](size)

    if custom_cases:
        base_dataset.extend(custom_cases)

    return base_dataset

def _create_basic_qa_dataset(size: int) -> List[Dict[str, str]]:
    """Basic Q&A test cases"""
    cases = [
        {
            "prompt": "What is the capital of France?",
            "expected": "Paris",
            "metadata": {"category": "geography", "difficulty": "easy"}
        },
        {
            "prompt": "Explain photosynthesis in one sentence.",
            "expected": "Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen.",
            "metadata": {"category": "science", "difficulty": "medium"}
        },
        {
            "prompt": "What is 15 + 27?",
            "expected": "42",
            "metadata": {"category": "math", "difficulty": "easy"}
        },
        {
            "prompt": "Who wrote 'Romeo and Juliet'?",
            "expected": "William Shakespeare",
            "metadata": {"category": "literature", "difficulty": "easy"}
        },
        {
            "prompt": "What is the largest planet in our solar system?",
            "expected": "Jupiter",
            "metadata": {"category": "astronomy", "difficulty": "easy"}
        },
        {
            "prompt": "Define machine learning in simple terms.",
            "expected": "Machine learning is a type of artificial intelligence where computers learn patterns from data to make predictions or decisions without being explicitly programmed.",
            "metadata": {"category": "technology", "difficulty": "medium"}
        },
        {
            "prompt": "What year did World War II end?",
            "expected": "1945",
            "metadata": {"category": "history", "difficulty": "easy"}
        },
        {
            "prompt": "What is the chemical symbol for gold?",
            "expected": "Au",
            "metadata": {"category": "chemistry", "difficulty": "medium"}
        },
        {
            "prompt": "Name three types of renewable energy.",
            "expected": "Solar energy, wind energy, and hydroelectric energy",
            "metadata": {"category": "environment", "difficulty": "medium"}
        },
        {
            "prompt": "What is the speed of light?",
            "expected": "Approximately 299,792,458 meters per second",
            "metadata": {"category": "physics", "difficulty": "hard"}
        }
    ]

    return cases[:size]

def _create_reasoning_dataset(size: int) -> List[Dict[str, str]]:
    """Reasoning and logic test cases"""
    cases = [
        {
            "prompt": "If all roses are flowers and all flowers are plants, are all roses plants?",
            "expected": "Yes, all roses are plants. This follows from the logical chain: roses → flowers → plants.",
            "metadata": {"category": "logic", "difficulty": "medium"}
        },
        {
            "prompt": "A farmer has 17 sheep. All but 9 die. How many sheep are left?",
            "expected": "9 sheep are left. 'All but 9' means 9 survived.",
            "metadata": {"category": "word_problem", "difficulty": "medium"}
        },
        {
            "prompt": "What comes next in this sequence: 2, 4, 8, 16, ?",
            "expected": "32. Each number is doubled from the previous one.",
            "metadata": {"category": "pattern", "difficulty": "easy"}
        },
        {
            "prompt": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
            "expected": "5 minutes. Each machine makes 1 widget in 5 minutes, so 100 machines make 100 widgets in the same 5 minutes.",
            "metadata": {"category": "logic", "difficulty": "hard"}
        },
        {
            "prompt": "You have a 3-liter jug and a 5-liter jug. How can you measure exactly 4 liters?",
            "expected": "Fill the 5L jug, pour into 3L jug (leaving 2L in 5L jug). Empty 3L jug, pour the 2L from 5L jug into 3L jug. Fill 5L jug again, pour into 3L jug until full (1L poured, 4L remains in 5L jug).",
            "metadata": {"category": "puzzle", "difficulty": "hard"}
        },
        {
            "prompt": "If today is Monday, what day will it be 100 days from now?",
            "expected": "Wednesday. 100 days = 14 weeks + 2 days. So it will be Monday + 2 days = Wednesday.",
            "metadata": {"category": "calendar", "difficulty": "medium"}
        },
        {
            "prompt": "Three friends split a bill. The bill is $30. If they each pay equally, how much does each person pay?",
            "expected": "$10. $30 divided by 3 people equals $10 per person.",
            "metadata": {"category": "division", "difficulty": "easy"}
        },
        {
            "prompt": "A bat and a ball cost $1.10 in total. The bat costs $1 more than the ball. How much does the ball cost?",
            "expected": "The ball costs $0.05. If ball = x, then bat = x + $1. So x + (x + $1) = $1.10, which gives 2x = $0.10, so x = $0.05.",
            "metadata": {"category": "algebra", "difficulty": "hard"}
        }
    ]

    return cases[:size]

def _create_tool_usage_dataset(size: int) -> List[Dict[str, str]]:
    """Test cases for tool usage and API calls"""
    cases = [
        {
            "prompt": "Search for information about climate change and summarize the main points.",
            "expected": "I would search for recent information about climate change and provide a summary covering key aspects like causes, effects, and potential solutions.",
            "metadata": {"category": "search_tool", "difficulty": "medium"}
        },
        {
            "prompt": "Calculate the compound interest on $1000 at 5% annual rate for 3 years.",
            "expected": "Using the compound interest formula A = P(1+r)^t: $1000 × (1.05)^3 = $1157.63. The compound interest is $157.63.",
            "metadata": {"category": "calculator", "difficulty": "medium"}
        },
        {
            "prompt": "What's the weather forecast for Tokyo tomorrow?",
            "expected": "I would check the weather API for Tokyo and provide tomorrow's forecast including temperature, conditions, and precipitation probability.",
            "metadata": {"category": "weather_api", "difficulty": "easy"}
        },
        {
            "prompt": "Translate 'Hello, how are you?' to Spanish.",
            "expected": "Hola, ¿cómo estás?",
            "metadata": {"category": "translation", "difficulty": "easy"}
        },
        {
            "prompt": "Find the latest news about artificial intelligence breakthroughs.",
            "expected": "I would search for recent AI news and provide a summary of the latest breakthroughs and developments in the field.",
            "metadata": {"category": "news_search", "difficulty": "medium"}
        }
    ]

    return cases[:size]

def _create_summarization_dataset(size: int) -> List[Dict[str, str]]:
    """Text summarization test cases"""
    cases = [
        {
            "prompt": "Summarize this text in one sentence: 'Machine learning is a subset of artificial intelligence that focuses on developing algorithms that can learn and make decisions from data. It involves training models on large datasets to recognize patterns and make predictions. Applications include image recognition, natural language processing, and recommendation systems.'",
            "expected": "Machine learning is an AI subset that develops algorithms to learn from data and make predictions, with applications in image recognition, natural language processing, and recommendation systems.",
            "metadata": {"category": "tech_summary", "difficulty": "medium"}
        },
        {
            "prompt": "Provide a brief summary of the key benefits of renewable energy.",
            "expected": "Renewable energy offers environmental benefits by reducing greenhouse gas emissions, provides energy security through domestic resources, creates jobs, and has become increasingly cost-competitive with fossil fuels.",
            "metadata": {"category": "environment_summary", "difficulty": "medium"}
        }
    ]

    return cases[:size]

def _create_code_generation_dataset(size: int) -> List[Dict[str, str]]:
    """Code generation test cases"""
    cases = [
        {
            "prompt": "Write a Python function to calculate the factorial of a number.",
            "expected": "def factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    return n * factorial(n - 1)",
            "metadata": {"category": "python", "difficulty": "medium"}
        },
        {
            "prompt": "Create a function to check if a string is a palindrome.",
            "expected": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]",
            "metadata": {"category": "python", "difficulty": "easy"}
        },
        {
            "prompt": "Write a SQL query to find all users who registered in the last 30 days.",
            "expected": "SELECT * FROM users WHERE registration_date >= CURRENT_DATE - INTERVAL 30 DAY;",
            "metadata": {"category": "sql", "difficulty": "medium"}
        }
    ]

    return cases[:size]

def _create_multi_language_dataset(size: int) -> List[Dict[str, str]]:
    """Multi-language test cases"""
    cases = [
        {
            "prompt": "Responda em português: Qual é a capital do Brasil?",
            "expected": "A capital do Brasil é Brasília.",
            "metadata": {"category": "portuguese", "difficulty": "easy"}
        },
        {
            "prompt": "¿Cuál es la fórmula del área de un círculo?",
            "expected": "La fórmula del área de un círculo es π × r², donde r es el radio.",
            "metadata": {"category": "spanish", "difficulty": "medium"}
        }
    ]

    return cases[:size]

def load_eval_dataset(file_path: str) -> List[Dict[str, str]]:
    """
    Load evaluation dataset from file

    Args:
        file_path: Path to dataset file (JSON)

    Returns:
        List of test cases
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Support different file formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "test_cases" in data:
        return data["test_cases"]
    else:
        raise ValueError(f"Invalid dataset format in {file_path}")

def save_eval_dataset(dataset: List[Dict[str, str]], file_path: str):
    """
    Save evaluation dataset to file

    Args:
        dataset: List of test cases
        file_path: Path to save dataset
    """
    output_data = {
        "test_cases": dataset,
        "metadata": {
            "created_at": "auto-generated",
            "total_cases": len(dataset)
        }
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

# Pre-built datasets for common scenarios
CHAT_SCENARIOS = {
    "simple_chat": create_eval_dataset("basic_qa", 5),
    "reasoning_chat": create_eval_dataset("reasoning", 5),
    "tool_assisted_chat": create_eval_dataset("tool_usage", 5)
}

def get_chat_scenario(scenario_name: str) -> List[Dict[str, str]]:
    """Get pre-built chat scenario dataset"""
    if scenario_name not in CHAT_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(CHAT_SCENARIOS.keys())}")

    return CHAT_SCENARIOS[scenario_name]