from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q

from .models import Message
from .forms import MessageForm

from authCustom.models import CustomUser
from mySpecialist.models import SpecialistPatientHistory


# === PANEL MESSENGERA ===

@login_required
def messenger_panel(request):
    return render(request, 'messaging/panel_messages.html')


# === LISTA KONTAKTÓW Z PODGLĄDEM I ILOŚCIĄ NOWYCH WIADOMOŚCI ===

@login_required
def get_contacts(request):
    user = request.user
    query = request.GET.get("search", "").strip().lower()

    if user.is_patient():
        contacts = CustomUser.objects.filter(role='specialist')
    else:
        contacts = CustomUser.objects.filter(
            Q(role='patient') & Q(specialist_history__specialist=user)
        ).distinct()

    if query:
        contacts = contacts.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        )

    result = []
    for contact in contacts:
        last_msg = Message.objects.filter(
            Q(sender=user, recipient=contact) |
            Q(sender=contact, recipient=user)
        ).order_by('-sent_at').first()

        unread_count = Message.objects.filter(
            sender=contact,
            recipient=user,
            is_read=False
        ).count()

        result.append({
            'id': contact.id,
            'name': contact.get_full_name() or contact.username,
            'last_message': last_msg.content if last_msg else '',
            'last_time': last_msg.sent_at.strftime('%Y-%m-%d %H:%M') if last_msg else '',
            'unread': unread_count,
        })

    return JsonResponse({'contacts': result})


# === POBIERANIE ROZMOWY Z KONTAKTEM ===

@login_required
def get_conversation(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)

    if request.user.is_specialist():
        allowed = SpecialistPatientHistory.objects.filter(
            specialist=request.user, patient=other_user
        ).exists()
    elif request.user.is_patient():
        allowed = other_user.role == 'specialist'
    else:
        allowed = False

    if not allowed:
        return HttpResponseBadRequest("Brak dostępu do rozmowy")

    # Oznacz nieprzeczytane wiadomości jako przeczytane
    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    messages = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('sent_at')

    data = [
        {
            'sender': msg.sender.get_full_name() or msg.sender.username,
            'text': msg.content,
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M'),
            'is_own': msg.sender == request.user
        }
        for msg in messages
    ]

    return JsonResponse({'messages': data})


# === WYSYŁANIE WIADOMOŚCI ===

@login_required
def send_message_ajax(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Tylko POST")

    recipient_id = request.POST.get('recipient_id')
    content = request.POST.get('content')

    if not recipient_id or not content:
        return HttpResponseBadRequest("Brak danych")

    recipient = get_object_or_404(CustomUser, id=recipient_id)

    if request.user.is_specialist():
        allowed = SpecialistPatientHistory.objects.filter(
            specialist=request.user, patient=recipient
        ).exists()
    elif request.user.is_patient():
        allowed = recipient.role == 'specialist'
    else:
        allowed = False

    if not allowed:
        return HttpResponseBadRequest("Nie możesz pisać do tego użytkownika")

    message = Message.objects.create(
        sender=request.user,
        recipient=recipient,
        content=content,
        body=content,
        subject="(bez tematu)"
    )

    return JsonResponse({
        'status': 'ok',
        'sent_at': message.sent_at.strftime('%Y-%m-%d %H:%M')
    })


# === ZLICZANIE WSZYSTKICH NIEPRZECZYTANYCH WIADOMOŚCI ===

@login_required
def unread_count(request):
    count = Message.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})
