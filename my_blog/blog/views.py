from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery, TrigramSimilarity
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from taggit.models import Tag

from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post, Comment


class PostListView(ListView):
    # queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

    def get_queryset(self, **kwargs):
        queryset = Post.published.all()
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags__in=[tag])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_slug = self.kwargs.get('tag_slug')

        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            context['tag'] = tag
            print(context['tag'])
        return context


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                             publish_date__year=year, publish_date__month=month, publish_date__day=day,
                             status=Post.Status.PUBLISHED)
    comments = post.comments.filter(active=True)
    form = CommentForm()

    # List of similar posts
    similar_posts = post.tags.similar_objects()[:4]
    return render(request, 'blog/post/detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'similar_posts': similar_posts
    })


def post_share(request, pk):
    post = get_object_or_404(Post, pk=pk, status=Post.Status.PUBLISHED)

    form = EmailPostForm()
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cleaned_form = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )

            subject = f"{cleaned_form['name']} recommends you to read {post.title}"
            message = f"Read {post.title} at the {post_url}\n\n"
            # add comments to the message only if provided
            if cleaned_form['comments']:
                message += f"{cleaned_form['name']}'s comments: {cleaned_form['comments']}"

            sent = send_mail(subject, message,
                             from_email=cleaned_form['sender_email'], recipient_list=[cleaned_form['recipient_email']])

    return render(request, 'blog/post/share.html', {
        'post': post,
        'form': form,
        'sent': sent,
    })


@require_POST
def post_comment(request, pk):
    post = get_object_or_404(Post, pk=pk, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = User.objects.get(pk=1)
        comment.save()

    return render(request, 'blog/post/comment.html', {
        'post': post,
        'form': form,
        'comment': comment
    })


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    # GET request to see query param in URL
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.published.annotate(
                # search=search_vector,
                similarity=TrigramSimilarity('title', query),
                rank=SearchRank(search_vector, search_query)
            ).filter(similarity__gt=0.1).order_by('-similarity')

    return render(request, 'blog/post/search.html', {
        'form': form,
        'query': query,
        'results': results
    })
