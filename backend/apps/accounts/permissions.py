from rest_framework import permissions
from django.contrib.auth.models import Group




class IsSuperAdmin(permissions.BasePermission):
    

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.groups.filter(name='SuperAdmin').exists()


    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='SuperAdmin').exists()
    
    



class IsComplexManager(permissions.BasePermission):
        
        def has_permission(self, request, view):
            return (request.user.is_authenticated and 
                request.user.is_complex_manager and
                not request.user.is_super_admin) 



class IsRegularUser(permissions.BasePermission):
        def has_permission(self, request, view):
            return (request.user.is_authenticated and 
                not request.user.is_super_admin and
                not request.user.is_complex_manager)
    
    
        
        
        
        
       


    


    