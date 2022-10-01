from django.urls import path
from .Routes import views,home,Profile,chatbot,AgriSchool

urlpatterns = []

def add_path( paths : list ) -> None:
    for i in paths :
        for j in i:
            urlpatterns.append(j)
        
#ChatRoom Paths

Home = [
    path('', home.home),
]
Admin = [
   path("home", home.home, name='home'),
   path("Donate/", home.donate, name='Donate'),
   path("joinUs/", home.joinUs, name='joinUs'),
   path("login1", home.loginUser, name='login'),
   path("logout1", home.logoutUser, name='logout'),
   path("signup1", home.signupUser, name='signup'),
   path("Admin/", home.Admin, name='Admin'),
]
ChatRoom = [
    path('chat_lobby', views.lobby),
    path('room/', views.room),
    path('get_token/', views.getToken),
    path('create_member/', views.createMember),
    path('get_member/', views.getMember),
    path('delete_member/', views.deleteMember),
]

profile = [
    path('login', Profile.index, name='index'),
    path('settings', Profile.settings, name='settings'),
    path('upload', Profile.upload, name='upload'),
    path('follow', Profile.follow, name='follow'),
    path('search', Profile.search, name='search'),
    path('profile/<str:pk>', Profile.profile, name='profile'),
    path('like-post', Profile.like_post, name='like-post'),
    path('signup', Profile.signup, name='signup'),
    path('signin', Profile.signin, name='signin'),
    path('logout', Profile.logout, name='logout'),
]
Chatbot = [
    path('chatbot', chatbot.chatbot),
    path('cource', chatbot.cource),
    path('bot', chatbot.bot),
    path('get_username', chatbot.get_username),

]

#Adding all paths to main path
Agrischool = [path('Agri', AgriSchool.Agri),]

add_path([profile,Home,ChatRoom,Chatbot,Admin,Agrischool])