from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import File
from .serializers import FileSerializer
from django.db.models import Q
from django.utils.dateparse import parse_datetime


# Create your views here.

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def get_queryset(self):
        queryset = File.objects.all()
        filename = self.request.query_params.get('filename')
        file_type = self.request.query_params.get('file_type')
        min_size = self.request.query_params.get('min_size')
        max_size = self.request.query_params.get('max_size')
        uploaded_after = self.request.query_params.get('uploaded_after')
        uploaded_before = self.request.query_params.get('uploaded_before')

        if filename:
            queryset = queryset.filter(original_filename__icontains=filename)
        if file_type:
            queryset = queryset.filter(file_type__icontains=file_type)
        if min_size:
            queryset = queryset.filter(size__gte=min_size)
        if max_size:
            queryset = queryset.filter(size__lte=max_size)
        if uploaded_after:
            queryset = queryset.filter(uploaded_at__gte=parse_datetime(uploaded_after))
        if uploaded_before:
            queryset = queryset.filter(uploaded_at__lte=parse_datetime(uploaded_before))

        return queryset
    

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Calculate file hash
        file_hash = calculate_file_hash(file_obj)

        # 2. Check if file with same hash exists
        try:
            existing_file = File.objects.get(hash=file_hash)
            serializer = self.get_serializer(existing_file)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except File.DoesNotExist:
            pass

        # 3. Save new file
        data = {
            'file': file_obj,
            'original_filename': file_obj.name,
            'file_type': file_obj.content_type,
            'size': file_obj.size,
            'hash': file_hash
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = {
            'file': file_obj,
            'original_filename': file_obj.name,
            'file_type': file_obj.content_type,
            'size': file_obj.size
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    


# views.py
import hashlib

def calculate_file_hash(file_obj):
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


