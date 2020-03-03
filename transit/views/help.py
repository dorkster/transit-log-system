from django.shortcuts import render, get_object_or_404

def helpMain(request):
    return helpPage(request, slug='')

def helpPage(request, slug):
    if slug == '':
        slug = 'getting-started'

    topics = (
        ('Getting Started', 'getting-started'),
        ('Drivers, Vehicles, and Trip Types', 'drivers-vehicles-and-trip-types'),
        ('Clients, Destinations, and Templates', 'clients-destinations-and-templates'),
        ('Editing the Schedule', 'editing-the-schedule'),
        ('Using the Schedule', 'using-the-schedule'),
        ('Vehicle Status', 'vehicle-status'),
        ('Monthly Reports', 'monthly-reports'),
    )

    topic_prev = None
    topic_next = None
    topic_current = None

    for i in range(0, len(topics)):
        if slug == topics[i][1]:
            topic_current = topics[i]

            if i > 0:
                topic_prev = topics[i-1]
            if i < (len(topics) - 1):
                topic_next = topics[i+1]

            break

    context = {
        'topic_current': topic_current,
        'topic_prev': topic_prev,
        'topic_next': topic_next,
        'topics': topics,
    }
    return render(request, 'help/' + slug + '.html', context)

