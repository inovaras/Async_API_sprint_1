def template_cache_key(pagination, sort, func_name: str) -> str:
    # TODO сделать проверку на наличие sort and filter
    sort = sort.sort_by
    pagination_query = f"{pagination['page']}_{pagination['per_page']}"
    template = f"{func_name}_{pagination_query}_{sort}"

    return template

"""    func_name = inspect.currentframe().f_code.co_name
    template = template_cache_key(pagination=pagination, sort=sort, func_name=func_name)"""