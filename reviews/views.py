from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from core.models import UserProfile, Avis
from core.mongo import get_db


@login_required(login_url='/login/')
def reviews_list(request, slug):
    target_profile = UserProfile.objects.select_related('user').get(slug=slug)
    target_user = target_profile.user
    if not target_profile.slug:
        target_profile.save()

    qs = Avis.objects.filter(reviewee=target_user)

    # filters
    def clamp_int(param):
        try:
            v = int(request.GET.get(param, 0))
            return min(5, max(0, v))
        except (TypeError, ValueError):
            return 0
    min_note = clamp_int('min_note')
    min_comm = clamp_int('min_comm')
    min_fiab = clamp_int('min_fiab')
    min_symp = clamp_int('min_symp')
    if min_note:
        qs = qs.filter(note__gte=min_note)
    if min_comm:
        qs = qs.filter(communication__gte=min_comm)
    if min_fiab:
        qs = qs.filter(fiabilite__gte=min_fiab)
    if min_symp:
        qs = qs.filter(sympathie__gte=min_symp)

    sort = request.GET.get('sort', 'recent')
    order_map = {
        'recent': '-created_at',
        'oldest': 'created_at',
        'note_desc': '-note',
        'note_asc': 'note',
        'comm_desc': '-communication',
        'fiab_desc': '-fiabilite',
        'symp_desc': '-sympathie',
    }
    qs = qs.order_by(order_map.get(sort, '-created_at'))

    stats = Avis.objects.filter(reviewee=target_user).aggregate(
        avg_note=Avg('note'),
        avg_comm=Avg('communication'),
        avg_fiab=Avg('fiabilite'),
        avg_symp=Avg('sympathie'),
        reviews_count=Count('id')
    )
    def pct(v):
        return int(round(((v or 0) / 5) * 100))

    from django.core.paginator import Paginator
    paginator = Paginator(qs, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    existing_by_me = None
    can_review = False
    if request.user.is_authenticated and request.user != target_user:
        existing_by_me = Avis.objects.filter(reviewer=request.user, reviewee=target_user).first()
        try:
            db = get_db()
            me = db.profiles.find_one({'user_id': request.user.id}) or {}
            him = db.profiles.find_one({'user_id': target_user.id}) or {}
            can_review = (
                (target_user.id in (me.get('following', []))) and
                (request.user.id in (him.get('following', []))) and
                (existing_by_me is None)
            )
        except Exception:
            can_review = False

    context = {
        'target_user': target_user,
        'target_profile': target_profile,
        'profile': target_profile,
        'slug': target_profile.slug,
        'page_obj': page_obj,
        'avis_page': page_obj,
        'sort': sort,
        'min_note': min_note,
        'min_comm': min_comm,
        'min_fiab': min_fiab,
        'min_symp': min_symp,
        'avg_note': round(stats['avg_note'] or 0, 2),
        'avg_comm': round(stats['avg_comm'] or 0, 2),
        'avg_fiab': round(stats['avg_fiab'] or 0, 2),
        'avg_symp': round(stats['avg_symp'] or 0, 2),
        'reviews_count': stats['reviews_count'] or 0,
        'avis_count': stats['reviews_count'] or 0,
        'avg_note_pct': pct(stats['avg_note']),
        'avg_comm_pct': pct(stats['avg_comm']),
        'avg_fiab_pct': pct(stats['avg_fiab']),
        'avg_symp_pct': pct(stats['avg_symp']),
        'can_review': can_review,
        'existing_by_me': existing_by_me,
    }
    return render(request, 'reviews/list.html', context)


@login_required(login_url='/login/')
def review_create(request, slug):
    target_profile = UserProfile.objects.select_related('user').get(slug=slug)
    target_user = target_profile.user
    if not target_profile.slug:
        target_profile.save()
    if request.method == 'POST':
        try:
            note = int(request.POST.get('note'))
            communication = int(request.POST.get('communication'))
            fiabilite = int(request.POST.get('fiabilite'))
            sympathie = int(request.POST.get('sympathie'))
        except Exception:
            messages.error(request, 'Notes invalides.')
            return redirect('reviews:review_create', slug=slug)
        commentaire = request.POST.get('commentaire', '').strip()

        avis = Avis(
            reviewer=request.user,
            reviewee=target_user,
            note=note,
            communication=communication,
            fiabilite=fiabilite,
            sympathie=sympathie,
            commentaire=commentaire or None,
        )
        try:
            avis.save()
            messages.success(request, 'Votre avis a été enregistré.')
            return redirect('reviews:reviews_list', slug=slug)
        except Exception as e:
            messages.error(request, str(e))
            return redirect('reviews:review_create', slug=slug)

    return render(request, 'reviews/create.html', {
        'target_user': target_user,
        'target_profile': target_profile,
        'profile': target_profile,
        'slug': target_profile.slug,
    })


@login_required(login_url='/login/')
def review_edit(request, slug, review_id):
    target_profile = UserProfile.objects.select_related('user').get(slug=slug)
    review = Avis.objects.get(id=review_id)
    if review.reviewer_id != request.user.id:
        messages.error(request, "Vous ne pouvez modifier que vos propres avis.")
        return redirect('reviews:reviews_list', slug=slug)

    if request.method == 'POST':
        try:
            review.note = int(request.POST.get('note'))
            review.communication = int(request.POST.get('communication'))
            review.fiabilite = int(request.POST.get('fiabilite'))
            review.sympathie = int(request.POST.get('sympathie'))
            review.commentaire = (request.POST.get('commentaire', '').strip()) or None
            review.save()
            messages.success(request, 'Avis modifié.')
            return redirect('reviews:reviews_list', slug=slug)
        except Exception as e:
            messages.error(request, str(e))
            return redirect('reviews:review_edit', slug=slug, review_id=review_id)

    return render(request, 'reviews/edit.html', {
        'profile': target_profile,
        'avis': review,
        'slug': slug,
    })


@login_required(login_url='/login/')
def review_delete(request, slug, review_id):
    review = Avis.objects.get(id=review_id)
    if review.reviewer_id != request.user.id:
        messages.error(request, "Vous ne pouvez supprimer que vos propres avis.")
        return redirect('reviews:reviews_list', slug=slug)
    review.delete()
    messages.success(request, 'Avis supprimé.')
    return redirect('reviews:reviews_list', slug=slug)

