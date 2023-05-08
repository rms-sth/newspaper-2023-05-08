from datetime import timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView, View

from newspaper.forms import CommentForm, ContactForm, NewsletterForm
from newspaper.models import Category, Post, Tag


class HomeView(ListView):
    model = Post
    queryset = Post.objects.filter(
        status="active", published_at__isnull=False
    ).order_by("-published_at")
    template_name = "aznews/main/home/home.html"
    context_object_name = "posts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_post"] = (
            Post.objects.filter(status="active", published_at__isnull=False)
            .order_by("-views_count")
            .first()
        )
        context["featured_posts"] = Post.objects.filter(
            status="active", published_at__isnull=False
        ).order_by("-views_count")[2:5]

        one_week_ago = timezone.now() - timedelta(days=7)
        context["weekly_top_posts"] = Post.objects.filter(
            status="active",
            published_at__isnull=False,
            published_at__gte=one_week_ago,
        ).order_by("-published_at")[:7]

        return context


class AboutView(TemplateView):
    template_name = "aznews/about.html"


class ContactView(View):
    template_name = "aznews/main/contact.html"

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
        )

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Successfully submitted your query. We will contact you soon."
            )
            return render(
                request,
                self.template_name,
            )
        else:
            messages.error(
                request,
                "Cannot submitted your query. Please make sure your forms are valid.",
            )
            return render(
                request,
                self.template_name,
                {"form": form},
            )


class PostListView(ListView):
    model = Post
    template_name = "aznews/main/list/list.html"
    context_object_name = "posts"
    queryset = Post.objects.filter(
        status="active", published_at__isnull=False
    ).order_by("-published_at")
    paginate_by = 2


class PostDetailView(DetailView):
    model = Post
    template_name = "aznews/main/detail/detail.html"
    context_object_name = "post"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # current viewed post
        obj = self.get_object()  # 4
        obj.views_count += 1
        obj.save()

        # 1,2,3, => 3, 2, 1 => 3
        context["previous_post"] = (
            Post.objects.filter(
                status="active", published_at__isnull=False, id__lt=obj.id
            )
            .order_by("-id")
            .first()
        )

        # 5, 6, 7, 8 .... => 5, 6, 7, 8 ... => 5
        context["next_post"] = (
            Post.objects.filter(
                status="active", published_at__isnull=False, id__gt=obj.id
            )
            .order_by("id")
            .first()
        )

        return context


class PostByCategoryView(ListView):
    model = Post
    template_name = "aznews/main/list/list.html"
    context_object_name = "posts"
    paginate_by = 2

    def get_queryset(self):
        query = super().get_queryset()
        query = query.filter(
            status="active",
            published_at__isnull=False,
            category=self.kwargs["category_id"],
        ).order_by("-published_at")
        return query


class PostByTagView(ListView):
    model = Post
    template_name = "aznews/main/list/list.html"
    context_object_name = "posts"
    paginate_by = 2

    def get_queryset(self):
        query = super().get_queryset()
        query = query.filter(
            status="active",
            published_at__isnull=False,
            tag=self.kwargs["tag_id"],
        ).order_by("-published_at")
        return query


class NewsletterView(View):
    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get("x-requested-with")
        if is_ajax == "XMLHttpRequest":
            form = NewsletterForm(request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Successfully submitted to our newsletter.",
                    },
                    status=201,
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Email is not valid.",
                    },
                    status=400,
                )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Cannot process. Must be an AJAX request.",
                },
                status=400,
            )


class CommentView(View):
    template_name = "aznews/main/detail/detail.html"

    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        post_id = request.POST["post"]
        if form.is_valid():
            form.save()
            return redirect("post-detail", post_id)
        else:
            post = Post.objects.get(pk=post_id)
            return render(
                request,
                self.template_name,
                {"post": post, "form": form},
            )


from django.core.paginator import PageNotAnInteger, Paginator
from django.db.models import Q


class PostSearchView(View):
    template_name = "aznews/main/list/search_list.html"

    def get(self, request, *args, **kwargs):
        query = request.GET.get("query")
        post_list = Post.objects.filter(
            (Q(status="active") & Q(published_at__isnull=False))
            & (Q(title__icontains=query) | Q(content__icontains=query)),
        )
        
        # function based views
        page = request.GET.get("page", 1)
        paginator = Paginator(post_list, 1)
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)

        return render(
            request,
            self.template_name,
            {"page_obj": posts, "query": query},
        )
