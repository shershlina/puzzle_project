from django.core.paginator import Paginator
from puzzlife.settings import POSTS_NUM


def get_page(queryset, page: int = 1):
    paginator = Paginator(queryset, POSTS_NUM)
    return paginator.get_page(page)
