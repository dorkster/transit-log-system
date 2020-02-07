from django.shortcuts import render, get_object_or_404

from transit.models import HelpPage

from django.contrib.auth.decorators import permission_required

def helpMain(request):
    return helpPage(request, slug='')

@permission_required(['transit.view_helppage'])
def helpPage(request, slug):
    topics = HelpPage.objects.all()

    if slug == '':
        slug = 'getting-started'

    slug_pages = HelpPage.objects.filter(slug=slug)

    if len(slug_pages) == 0 and len(topics) > 0:
        current = topics[0]
    elif len(slug_pages) == 0 and len(topics) == 0:
        current = HelpPage()
        current.title = 'No help topics found'
        current.body = '<p>Add help pages via the <a href="/admin/transit/helppage/">admin control panel</a>.</p>'
    else:
        current = slug_pages[0]

    page_previous = None
    previous_filter = HelpPage.objects.filter(sort_index=current.sort_index-1)
    if len(previous_filter) > 0:
        page_previous = previous_filter[0]

    page_next = None
    next_filter = HelpPage.objects.filter(sort_index=current.sort_index+1)
    if len(next_filter) > 0:
        page_next = next_filter[0]

    context = {
        'current': current,
        'topics': topics,
        'previous': page_previous,
        'next': page_next,
    }
    return render(request, 'help.html', context)

