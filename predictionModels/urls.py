from django.urls import path
from . import views

app_name = "predictionModels"

urlpatterns = [
    # path('predict/xgb/', views.predict_xgb_view, name='predict_xgb'),
    # path('predict/bert/', views.predict_bert_view, name='predict_bert'),

    path("ml-lab/", views.ml_lab, name="ml_lab"),
    path("ml-lab/herbert/train/", views.train_herbert_from_ui, name="train_herbert"),
    path("ml-lab/xgboost/train/", views.train_xgboost_from_ui, name="train_xgboost"),
    path("ml-lab/rag/add-note/", views.add_note_from_ui, name="add_note"),

]
