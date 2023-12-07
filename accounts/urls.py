from django.urls import path
from .views import (LogoutView, UserProfileView, CardCreateView,
                    CardListView, deposit_card, StaffProfileView, make_payment, statement, deposit_approval,
                    deposit_approval_list, create_savings_goal,
                    review_savings_plan, savings_goal_list, edit_savings_goal, delete_savings_goal, EditUserAddressView,
                    AccountLoginView)

app_name = 'accounts'

urlpatterns = [
    path(
        'login/', AccountLoginView.as_view(), name='login'
    ),
    path(
        "logout/", LogoutView.as_view(),
        name="user_logout"
    ),
    path(
        "profile/", UserProfileView.as_view(),
        name="user_profile"
    ),
    path(
        "profile-edit/", EditUserAddressView.as_view(),
        name="edit_profile"
    ),
    path(
        "staff_profile/", StaffProfileView.as_view(),
        name="staff_profile"
    ),
    path(
        'make_payment/', make_payment, name='make_payment'
    ),
    path(
        'create_card/', CardCreateView.as_view(),
        name='create_card'
    ),
    path(
        'card_list/', CardListView.as_view(),
        name='card_list'
    ),
    path(
        'card_history/<int:card_id>', statement,
        name='card_history'
    ),
    path(
        'deposit_card/<int:card_id>', deposit_card,
        name='deposit_form'
    ),
    path(
        'deposit-approval/', deposit_approval_list, name='deposit_approval_list'
    ),
    path(
        'deposit-approval/<int:card_id>/', deposit_approval, name='deposit_approval'
    ),
    path(
        'savings-goal/create/', create_savings_goal, name='create_savings_goal'
    ),

    path(
        'savings-goal/detail/<int:goal_id>/', review_savings_plan, name='review_savings_plan'
    ),
    path(
        'savings-goal-list/', savings_goal_list, name='savings_goal_list'
    ),
    path(
        'edit_savings_goal/<int:goal_id>/', edit_savings_goal, name='edit_savings_goal'
    ),
    path(
        'delete_savings_goal/<int:goal_id>/', delete_savings_goal, name='delete_savings_goal'
    ),


]
