from rest_framework import serializers
from .models import CustomUser, Post

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'password', 'email')
        extra_kwargs = {'password':{'write_only': True},}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user 
    def update(self, instance, validated_data):
        
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  
        instance.save()
        return instance
 
class CreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'phone_number', 'profile_picture', 'about', 'background_picture', 'instagram', 'youtube', 'username')   

class PostSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()
    is_my = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = "__all__"
        extra_kwargs = {'author':{'read_only': True}, 'reports':{'read_only': True}}
    def get_likes(self, obj):
        return obj.likes.count()   
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.through.objects.filter(post_id=obj.id, customuser_id=request.user.id).exists()
        return False
    def get_is_reported(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reports.through.objects.filter(post_id=obj.id, customuser_id=request.user.id).exists()
        return False
    def get_is_my(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user == obj.author:
                return True
        return False        