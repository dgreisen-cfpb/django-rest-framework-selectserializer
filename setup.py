from setuptools import setup


setup(
    name='django-rest-framework-selectserializer',
    packages=['selectserializer'],
    version='0.1.0',
    description='Select/Exclude fields in Django Rest Framework Serializers',
    author='David Greisen',
    author_email='dgreisen@gmail.com',
    url='https://github.com/cfpb/django-rest-framework-selectserializer',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
    ],
    install_requires=[
        'Django>=1.4',
        'djangorestframework>=2.3'
    ]
)
