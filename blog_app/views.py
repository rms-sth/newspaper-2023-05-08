from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import HttpResponseRedirect, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from blog_app.forms import PostForm
from newspaper.models import Post


# Class based views
# CRUD
class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    queryset = Post.objects.filter(published_at__isnull=False).order_by("-published_at")
    context_object_name = "posts"


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        queryset = Post.objects.filter(pk=self.kwargs["pk"], published_at__isnull=False)
        return queryset


class DraftListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/draft_list.html"
    queryset = Post.objects.filter(published_at__isnull=True).order_by("-published_at")
    context_object_name = "posts"


class DraftDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = "blog/draft_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        queryset = Post.objects.filter(pk=self.kwargs["pk"], published_at__isnull=True)
        return queryset


class DraftPublishView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk, published_at__isnull=True)
        post.published_at = timezone.now()
        post.save()
        return HttpResponseRedirect("/")


class PostDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        post.delete()
        return HttpResponseRedirect("/")


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_create.html"
    success_url = reverse_lazy("draft-list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_create.html"
    success_url = reverse_lazy("post-list")

    def get_success_url(self):
        post = self.get_object()
        if post.published_at:
            return reverse_lazy("post-detail", kwargs={"pk": post.id})
        else:
            return reverse_lazy("draft-detail", kwargs={"pk": post.id})


# class PostUpdateView(LoginRequiredMixin, View):
#     def get(self, request, pk, *args, **kwargs):
#         post = Post.objects.get(pk=pk)
#         form = PostForm(instance=post)
#         return render(
#             request,
#             "blog/post_create.html",
#             {"form": form},
#         )

#     def post(self, request, pk, *args, **kwargs):
#         post = Post.objects.get(pk=pk)
#         form = PostForm(instance=post)
#         if request.method == "POST":
#             form = PostForm(
#                 request.POST, instance=post
#             )  # frontend bata ako data haleko form ma
#             if form.is_valid():
#                 post.save()
#                 if post.published_at:
#                     return redirect("post-detail", post.pk)
#                 else:
#                     return redirect("draft-detail", post.pk)
#             else:
#                 return render(
#                     request,
#                     "blog/post_create.html",
#                     {"form": form},
#                 )


# @login_required
def post_update(request, pk):
    post = Post.objects.get(pk=pk)
    form = PostForm(instance=post)
    if request.method == "POST":
        form = PostForm(
            request.POST, instance=post
        )  # frontend bata ako data haleko form ma
        if form.is_valid():
            post.save()
            if post.published_at:
                return redirect("post-detail", post.pk)
            else:
                return redirect("draft-detail", post.pk)
    return render(
        request,
        "blog/post_create.html",
        {"form": form},
    )
