def search_jobs(city: str, keyword: str,) -> str:
    return (
        f"Searching jobs in {city} "
        f"with keyword {keyword}."
    )

def get_company_info(
    company: str,
) -> str:
    return (
        f"Company information for {company}: "
        f"{company} is a technology company."
    )