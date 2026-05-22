from django.contrib.auth.backends import ModelBackend



class SuperAdminGroupBackend(ModelBackend):
    

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        
        
        if user_obj.groups.filter(name="SuperAdmin").exists():
            return True
        
        return super().has_perm(self, user_obj, obj)
    


    def has_module_perms(self, user_obj, app_label):
        if not user_obj.is_active:
            return False
        
        if user_obj.groups.filter(name="SuperAdmin").exists():
            return True
        
        return super().has_module_perms(user_obj, app_label)

        