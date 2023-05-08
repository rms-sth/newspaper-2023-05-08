from newspaper.models import Tag, Category, Post


def navigation(request):
    categories = Category.objects.all()[:5]
    tags = Tag.objects.all()[:10]
    trending_posts = Post.objects.filter(
        status="active", published_at__isnull=False
    ).order_by("-published_at", "-views_count")[:5]
    
    return {
        "tags": tags,
        "categories": categories,
        "trending_posts": trending_posts,
    }
