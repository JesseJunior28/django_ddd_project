"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from src.use_cases.branch.create_branch.view import CreateBranchView, LegacyCreateBranchView
from src.use_cases.product.create_product.view import CreateProductView
from src._app.health import live, ready
from src.use_cases.auth.login.view import LoginView
from src.use_cases.auth.refresh_token.view import RefreshTokenView
from src.use_cases.branch.list_branches.view import ListBranchesView
from src.use_cases.branch.get_branch.view import GetBranchView
from src.use_cases.user.get_user.view import GetUserView
from src.use_cases.user.list_users.view import ListUsersView
from src.use_cases.user.update_user.view import UpdateUserView

from src.use_cases.auth.register.view import RegisterView
from src.use_cases.auth.reset_password.view import ResetPasswordView
from src.use_cases.auth.send_reset_password_token.view import SendResetPasswordTokenView
from src.use_cases.branch.update_branch.view import UpdateBranchView
from src.use_cases.branch.delete_branch.view import DeleteBranchView
from src.use_cases.industry.views import IndustryView, DeleteIndustryView
from src.use_cases.zone.views import ZoneView, DepartmentView, LevelView, DeleteZoneView, DeleteDepartmentView, DeleteLevelView
from src.use_cases.product.contract_view import ProductContractView
from src.use_cases.product.exposition_view import ProductExpositionView
from src.use_cases.product.ranking_view import ProductRankingView
from src.use_cases.product.base_product_view import BaseProductView
from src.use_cases.planogram.views import (
    DeleteModuleView, DeleteShelfLevelView, DeleteShelfView,
    GetPlanogramsByDepartmentView, ListPlanogramsView, ModuleView, PlanogramView,
    ShelfLevelView, ShelfView, UpdateModuleSequenceView, UpdatePlanogramNameView,
    UpdatePlanogramStatusView, UpdateShelfLevelSequenceView, UpdateShelfLevelView,
    UpdateShelfSequenceView,
    GetPlanogramView, GetPlanogramMetricsView,
)
from src.use_cases.branch_layout.views import (
    BranchLayoutView, DeleteBranchLayoutView, ElementModuleConfigurationView,
    GenerateLayoutVersionCodeView, GetBranchLayoutView, GetBranchesByPlanogramView,
)
from src.use_cases.demand.views import DemandView, DemandStatusView, ExecutionOccurrenceView, CreateBranchExecutionView, ExecutionDetailsView, ListExecutionsView, UpdateExecutionStatusView, EditExecutionAuditView, NotificationView, NotificationViewedView, CreateRoutineDemandView, FinishRoutineExecutionView, UpdateRoutineExecutionStatusView, RoutineDemandListView, RoutineExecutionListView, RoutineExecutionDetailsView, ReviewQuestionView, CreateExecutionReviewView, DemandMetricsView

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("send-reset-password-token", SendResetPasswordTokenView.as_view(), name="send-reset-password-token"),
    path("reset-password", ResetPasswordView.as_view(), name="reset-password"),
    path("update-branch", UpdateBranchView.as_view(), name="update-branch"),
    path("delete-branch/<str:branch_id>", DeleteBranchView.as_view(), name="delete-branch"),
    path("create-branch", CreateBranchView.as_view(), name="create-branch-contract"),
    path("create-industry", IndustryView.as_view(), name="create-industry"),
    path("list-industries", IndustryView.as_view(), name="list-industries"),
    path("update-industry", IndustryView.as_view(), name="update-industry"),
    path("delete-industry/<str:industry_id>", DeleteIndustryView.as_view(), name="delete-industry"),
    path("create-zone", ZoneView.as_view()), path("list-zones", ZoneView.as_view()), path("update-zone", ZoneView.as_view()), path("delete-zone/<str:object_id>", DeleteZoneView.as_view()),
    path("create-department", DepartmentView.as_view()), path("list-departments", DepartmentView.as_view()), path("update-department", DepartmentView.as_view()), path("delete-department/<str:object_id>", DeleteDepartmentView.as_view()),
    path("create-level", LevelView.as_view()), path("list-department-levels/<str:department_id>", LevelView.as_view()), path("update-level", LevelView.as_view()), path("delete-level/<str:object_id>", DeleteLevelView.as_view()),
    path("create-product", ProductContractView.as_view(), name="create-product-contract"),
    path("update-product", ProductContractView.as_view(), name="update-product-contract"),
    path("list-products", ProductContractView.as_view(), name="list-products-contract"),
    path("add-product-exposition-detail", ProductExpositionView.as_view(), name="add-product-exposition-detail-contract"),
    path("list-products-by-level/<int:level_id>", ProductExpositionView.as_view(), name="list-products-by-level-contract"),
    path("update-product-exposition-detail", ProductExpositionView.as_view(), name="update-product-exposition-detail-contract"),
    path("delete-product-exposition-detail/<int:detail_id>", ProductExpositionView.as_view(), name="delete-product-exposition-detail-contract"),
    path("get-predefined-ranking-and-priority", ProductRankingView.as_view(), name="get-predefined-ranking-and-priority-contract"),
    path("update-exposition-ranking-and-priority", ProductExpositionView.as_view(), name="update-exposition-ranking-and-priority-contract"),
    path("import-level-exposition", ProductExpositionView.as_view(), name="import-level-exposition-contract"),
    path("list-base-products", BaseProductView.as_view(), name="list-base-products-contract"),
    path("get-total-base-products", BaseProductView.as_view(), name="get-total-base-products-contract"),
    path("create-planogram", PlanogramView.as_view(), name="create-planogram-contract"),
    path("create-module", ModuleView.as_view(), name="create-module-contract"),
    path("create-shelf", ShelfView.as_view(), name="create-shelf-contract"),
    path("add-shelf-level", ShelfLevelView.as_view(), name="add-shelf-level-contract"),
    path("delete-module/<str:module_id>", DeleteModuleView.as_view(), name="delete-module-contract"),
    path("delete-shelf/<str:shelf_id>", DeleteShelfView.as_view(), name="delete-shelf-contract"),
    path("delete-shelf-level/<str:id>", DeleteShelfLevelView.as_view(), name="delete-shelf-level-contract"),
    path("get-planograms-by-department", GetPlanogramsByDepartmentView.as_view(), name="get-planograms-by-department-contract"),
    path("get-planogram-view", GetPlanogramView.as_view(), name="get-planogram-view"),
    path("get-planogram-metrics/<str:planogram_id>", GetPlanogramMetricsView.as_view(), name="get-planogram-metrics"),
    path("list-planograms", ListPlanogramsView.as_view(), name="list-planograms-contract"),
    path("update-planogram-status/<str:id>", UpdatePlanogramStatusView.as_view(), name="update-planogram-status-contract"),
    path("update-module-sequence", UpdateModuleSequenceView.as_view(), name="update-module-sequence-contract"),
    path("update-planogram-name", UpdatePlanogramNameView.as_view(), name="update-planogram-name-contract"),
    path("update-shelf-level", UpdateShelfLevelView.as_view(), name="update-shelf-level-contract"),
    path("update-shelf-level-sequence", UpdateShelfLevelSequenceView.as_view(), name="update-shelf-level-sequence-contract"),
    path("update-shelf-sequence", UpdateShelfSequenceView.as_view(), name="update-shelf-sequence-contract"),
    path("create-branch-layout", BranchLayoutView.as_view(), name="create-branch-layout"),
    path("get-branch-layout", GetBranchLayoutView.as_view(), name="get-branch-layout"),
    path("edit-branch-layout", BranchLayoutView.as_view(), name="edit-branch-layout"),
    path("delete-branch-layout/<str:branch_id>", DeleteBranchLayoutView.as_view(), name="delete-branch-layout"),
    path("generate-layout-version-code", GenerateLayoutVersionCodeView.as_view(), name="generate-layout-version-code"),
    path("update-element-module-configuration", ElementModuleConfigurationView.as_view(), name="update-element-module-configuration"),
    path("get-branches-by-planogram", GetBranchesByPlanogramView.as_view(), name="get-branches-by-planogram"),
    path('create-demand', DemandView.as_view()), path('list-demands', DemandView.as_view()), path('update-demand-status/<str:id>', DemandStatusView.as_view()),
    path('get-execution-occurrence/<str:branch_id>', ExecutionOccurrenceView.as_view()),
    path('create-branch-execution', CreateBranchExecutionView.as_view()),
    path('get-execution-details/<str:execution_id>', ExecutionDetailsView.as_view()),
    path('list-executions', ListExecutionsView.as_view()),
    path('update-execution-status', UpdateExecutionStatusView.as_view()),
    path('edit-execution-audit', EditExecutionAuditView.as_view()),
    path('get-notifications', NotificationView.as_view()),
    path('update-notification-viewed-at/<str:notification_id>', NotificationViewedView.as_view()),
    path('create-routine-demand', CreateRoutineDemandView.as_view()),
    path('finish-routine-execution', FinishRoutineExecutionView.as_view()),
    path('update-routine-execution-status', UpdateRoutineExecutionStatusView.as_view()),
    path('list-routine-demands', RoutineDemandListView.as_view()),
    path('get-routine-demand-occurence/<str:branch_id>', RoutineDemandListView.as_view()),
    path('list-routine-executions', RoutineExecutionListView.as_view()),
    path('get-routine-execution-details/<str:execution_id>', RoutineExecutionDetailsView.as_view()),
    path('list-review-questions', ReviewQuestionView.as_view()),
    path('create-execution-review', CreateExecutionReviewView.as_view()),
    path('get-demand-metrics', DemandMetricsView.as_view()),
    path('get-branch/<str:branch_id>', GetBranchView.as_view(), name='get-branch'),
    path('get-user', GetUserView.as_view(), name='get-user'),
    path('list-users', ListUsersView.as_view(), name='list-users'),
    path('update-user', UpdateUserView.as_view(), name='update-user'),
    path('login', LoginView.as_view(), name='login'),
    path('refresh-token', RefreshTokenView.as_view(), name='refresh-token'),
    path('list-branches', ListBranchesView.as_view(), name='list-branches'),
    path('health/live', live, name='health-live'),
    path('health/ready', ready, name='health-ready'),
    path('admin/', admin.site.urls),
    path('branches/', LegacyCreateBranchView.as_view(), name='create-branch'),
    path("products/", CreateProductView.as_view(), name="create-product"),
]
