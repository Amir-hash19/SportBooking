from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth import get_user_model
from django.db import models




class CustomUserManager(BaseUserManager):
    def create_user(self, name, last_name, phone_number, password, email=None,  accepted_role=False, **extra_fields):
        if not phone_number:
            raise ValueError("phone number is required")
        
        if not name and not last_name:
            raise ValueError("Enter Name and lastname please!")    
      
        if not accepted_role:
            raise ValueError("please read and accept the roles before creating account!")
        
        if not password:
            raise ValueError("Password is required")
        
       
        user = self.model(
            name=name,
            lastname=last_name,
            phonenumber=phone_number,
            email=self.normalize_email(email) if email else None,
            accepted_role=accepted_role,  
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    

    def create_superuser(self, name, last_name, phone_number, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('accepted_role', True)  
        
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if not password:
            raise ValueError("Superuser must have a password")
        
       
        return self.create_user(
            name=name,
            lastname=last_name,
            phonenumber=phone_number,
            email=email,
            password=password,
            **extra_fields
        )



class UserAccount(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = PhoneNumberField(unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    accepted_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ['name','last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.name} - {self.last_name}"




class Profile(models.Model):
    user = models.OneToOneField(to=UserAccount, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='/media/', null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    GENDER_TYPE=(
        ("1", "MALE"),
        ("2", "FEMALE")
    )

    gender = models.CharField(max_length=10, choices=GENDER_TYPE)
    second_number = PhoneNumberField(unique=True, null=True, blank=True)
    sport_fame = models.TextField(null=True, blank=True)
    medical_fame = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name} {self.gender}"



