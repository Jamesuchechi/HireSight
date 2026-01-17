from django.core.management.base import BaseCommand
from apps.assessments.models import QuestionPool, SkillTest, AssessmentCategory
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed the database with sample questions and tests'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding questions and tests...')
        
        # Create Python questions
        python_questions = [
            {
                'skill_name': 'Python',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is the correct way to create a list in Python?',
                'options': ['list = []', 'list = ()', 'list = {}', 'list = <>'],
                'correct_answer': 0,
                'explanation': 'Square brackets [] are used to create lists in Python.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'Python',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which keyword is used to define a function in Python?',
                'options': ['function', 'def', 'func', 'define'],
                'correct_answer': 1,
                'explanation': 'The "def" keyword is used to define functions in Python.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'Python',
                'difficulty': 'INTERMEDIATE',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What does the "self" keyword represent in Python classes?',
                'options': [
                    'The class itself',
                    'The instance of the class',
                    'The parent class',
                    'A static variable'
                ],
                'correct_answer': 1,
                'explanation': '"self" represents the instance of the class and is used to access instance variables and methods.',
                'points': 15,
                'estimated_time_seconds': 45
            },
            {
                'skill_name': 'Python',
                'difficulty': 'INTERMEDIATE',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which of the following is a mutable data type in Python?',
                'options': ['tuple', 'string', 'list', 'int'],
                'correct_answer': 2,
                'explanation': 'Lists are mutable in Python, meaning their contents can be changed after creation.',
                'points': 15,
                'estimated_time_seconds': 45
            },
            {
                'skill_name': 'Python',
                'difficulty': 'ADVANCED',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is a decorator in Python?',
                'options': [
                    'A function that modifies another function',
                    'A design pattern',
                    'A type of class',
                    'A data structure'
                ],
                'correct_answer': 0,
                'explanation': 'Decorators are functions that modify the behavior of other functions or methods.',
                'points': 20,
                'estimated_time_seconds': 60
            },
        ]
        
        # Create JavaScript questions
        js_questions = [
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which keyword is used to declare a variable in JavaScript?',
                'options': ['var', 'let', 'const', 'All of the above'],
                'correct_answer': 3,
                'explanation': 'var, let, and const are all valid ways to declare variables in JavaScript.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is the output of typeof []?',
                'options': ['array', 'object', 'list', 'undefined'],
                'correct_answer': 1,
                'explanation': 'In JavaScript, arrays are actually objects, so typeof [] returns "object".',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'INTERMEDIATE',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is a closure in JavaScript?',
                'options': [
                    'A function that has access to its outer function scope',
                    'A way to close the browser window',
                    'A type of loop',
                    'A method to end execution'
                ],
                'correct_answer': 0,
                'explanation': 'A closure is a function that has access to variables from its outer (enclosing) function scope.',
                'points': 15,
                'estimated_time_seconds': 45
            },
        ]
        
        # Create React questions
        react_questions = [
            {
                'skill_name': 'React',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is JSX?',
                'options': [
                    'A JavaScript library',
                    'A syntax extension for JavaScript',
                    'A database',
                    'A CSS framework'
                ],
                'correct_answer': 1,
                'explanation': 'JSX is a syntax extension for JavaScript that lets you write HTML-like markup inside JavaScript.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'React',
                'difficulty': 'INTERMEDIATE',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What hook is used to manage state in functional components?',
                'options': ['useEffect', 'useState', 'useContext', 'useReducer'],
                'correct_answer': 1,
                'explanation': 'useState is the primary hook for managing state in functional React components.',
                'points': 15,
                'estimated_time_seconds': 45
            },
        ]
        
        # Seed questions
        all_questions = python_questions + js_questions + react_questions
        created_count = 0
        
        for q_data in all_questions:
            question, created = QuestionPool.objects.get_or_create(
                skill_name=q_data['skill_name'],
                question=q_data['question'],
                defaults=q_data
            )
            if created:
                created_count += 1
                question.is_verified = True
                question.save()
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} questions'))
        
        # Create tests
        tests = [
            {
                'title': 'Python Fundamentals',
                'skill_name': 'Python',
                'description': 'Test your knowledge of Python basics',
                'test_type': 'DYNAMIC',
                'difficulty': 'BEGINNER',
                'duration_minutes': 20,
                'passing_score': 70,
                'question_count': 10,
                'question_pool_filters': {'difficulty': 'BEGINNER', 'types': ['MULTIPLE_CHOICE']},
                'is_active': True,
                'is_featured': True
            },
            {
                'title': 'JavaScript Essentials',
                'skill_name': 'JavaScript',
                'description': 'Master JavaScript fundamentals',
                'test_type': 'DYNAMIC',
                'difficulty': 'BEGINNER',
                'duration_minutes': 20,
                'passing_score': 70,
                'question_count': 10,
                'question_pool_filters': {'difficulty': 'BEGINNER', 'types': ['MULTIPLE_CHOICE']},
                'is_active': True,
                'is_featured': True
            },
            {
                'title': 'React Basics',
                'skill_name': 'React',
                'description': 'Test your React fundamentals',
                'test_type': 'DYNAMIC',
                'difficulty': 'BEGINNER',
                'duration_minutes': 15,
                'passing_score': 70,
                'question_count': 8,
                'question_pool_filters': {'difficulty': 'BEGINNER', 'types': ['MULTIPLE_CHOICE']},
                'is_active': True,
                'is_featured': False
            },
        ]
        
        test_count = 0
        for test_data in tests:
            if not SkillTest.objects.filter(title=test_data['title']).exists():
                test = SkillTest.objects.create(**test_data)
                test_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {test_count} tests'))
        
        # Create categories
        categories = [
            {'name': 'Programming', 'slug': 'programming', 'icon': '💻', 'order': 1},
            {'name': 'Web Development', 'slug': 'web-development', 'icon': '🌐', 'order': 2},
            {'name': 'Data Science', 'slug': 'data-science', 'icon': '📊', 'order': 3},
        ]
        
        cat_count = 0
        for cat_data in categories:
            category, created = AssessmentCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                cat_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {cat_count} categories'))
        self.stdout.write(self.style.SUCCESS('✅ Database seeding complete!'))