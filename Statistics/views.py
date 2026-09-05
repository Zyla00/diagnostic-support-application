from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
import pandas as pd

from wellnessTracker.models import Day


@login_required
def my_statistics_view(request):
    return render(request, "Statistics/stats_dashboard.html")



class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'mood_chart.html'
    login_url = '/login/'
    redirect_field_name = 'next'



@login_required
def mood_scale_data(request):
    data = Day.objects.values_list('mood_scale__scale', flat=True)
    mood_scale_counts = pd.Series(data).value_counts().sort_index().to_dict()
    return JsonResponse(mood_scale_counts)


@login_required
def mood_chart(request):
    return render(request, 'mood_chart.html')
