from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Główny widok (np. offcanvas)
    path('', views.messenger_panel, name='panel'),


    # Klasyczne widoki (jeśli jeszcze korzystasz)
    # path('inbox/', views.inbox, name='inbox'),
    # path('sent/', views.sent_messages, name='sent'),
    # path('send/', views.send_message_form, name='send'),  # zmieniona funkcja (poniżej wyjaśnienie)

    # Messenger-style AJAX
    path('contacts/', views.get_contacts, name='contacts'),
    path('conversation/<int:user_id>/', views.get_conversation, name='conversation'),
    path('send-message/', views.send_message_ajax, name='send_ajax'),
    path('unread-count/', views.unread_count, name='unread_count'),


]
