from rest_framework import serializers
from .models import Follow
from apps.accounts.models import User


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for follow relationships.
    """
    display_name = serializers.SerializerMethodField()
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'account_type', 'account_type_display']
    
    def get_display_name(self, obj):
        return obj.get_display_name()


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for Follow model.
    """
    follower = UserMinimalSerializer(read_only=True)
    followed = UserMinimalSerializer(read_only=True)
    is_mutual = serializers.SerializerMethodField()
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'created_at', 'is_mutual']
        read_only_fields = ['created_at']
    
    def get_is_mutual(self, obj):
        return Follow.are_mutual_followers(obj.follower, obj.followed)


class FollowCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a follow relationship.
    """
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        """Validate that user exists and can be followed"""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        # Check if trying to follow self
        if user == self.context['request'].user:
            raise serializers.ValidationError("You cannot follow yourself")
        
        # Check if already following
        if Follow.objects.filter(
            follower=self.context['request'].user,
            followed=user
        ).exists():
            raise serializers.ValidationError("You are already following this user")
        
        return value
    
    def create(self, validated_data):
        """Create the follow relationship"""
        user = User.objects.get(id=validated_data['user_id'])
        return Follow.objects.create(
            follower=self.context['request'].user,
            followed=user
        )


class FollowStatsSerializer(serializers.Serializer):
    """
    Serializer for follow statistics.
    """
    follower_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    mutual_count = serializers.IntegerField()
    is_following = serializers.BooleanField(required=False)
    is_mutual = serializers.BooleanField(required=False)