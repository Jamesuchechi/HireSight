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
            {
                'skill_name': 'Python',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What does len([1, 2, 3]) return?',
                'options': ['1', '2', '3', 'Error'],
                'correct_answer': 2,
                'explanation': 'len() returns the number of items, so this list has three elements.',
                'points': 10,
                'estimated_time_seconds': 25
            },
            {
                'skill_name': 'Python',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which keyword starts a try/except block?',
                'options': ['try', 'catch', 'handle', 'except'],
                'correct_answer': 0,
                'explanation': 'A try block is needed before except handlers.',
                'points': 10,
                'estimated_time_seconds': 40
            },
            {
                'skill_name': 'Python',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'How do you import the datetime module?',
                'options': ['include datetime', 'import datetime', 'require datetime', 'using datetime'],
                'correct_answer': 1,
                'explanation': 'Python uses the import statement to bring in modules.',
                'points': 10,
                'estimated_time_seconds': 35
            },
            {
                'skill_name': 'Python',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which data type stores key-value pairs?',
                'options': ['list', 'tuple', 'dictionary', 'set'],
                'correct_answer': 2,
                'explanation': 'Dictionaries are unordered mappings between keys and values.',
                'points': 10,
                'estimated_time_seconds': 35
            },
            {
                'skill_name': 'Python',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which method adds a new value to the end of a list?',
                'options': ['push()', 'append()', 'add()', 'insert()'],
                'correct_answer': 1,
                'explanation': 'append() adds an item to the end of a list.',
                'points': 10,
                'estimated_time_seconds': 30
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
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which function converts a JSON string to an object?',
                'options': ['JSON.stringify', 'JSON.parse', 'JSON.convert', 'JSON.decode'],
                'correct_answer': 1,
                'explanation': 'JSON.parse() converts JSON text into a JavaScript value.',
                'points': 10,
                'estimated_time_seconds': 35
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which method adds an item to the end of an array?',
                'options': ['push', 'pop', 'shift', 'splice'],
                'correct_answer': 0,
                'explanation': 'push() appends one or more elements to the end of an array.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is the default value of an uninitialized variable?',
                'options': ['null', 'undefined', '0', '""'],
                'correct_answer': 1,
                'explanation': 'Variables declared without assignment are undefined.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which keyword declares a block-scoped variable that can be reassigned?',
                'options': ['var', 'const', 'let', 'static'],
                'correct_answer': 2,
                'explanation': 'let creates block-scoped bindings whose value can change.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What does document.getElementById do?',
                'options': ['Creates a new DOM element', 'Selects an element by ID', 'Deletes an element', 'Sets styles directly'],
                'correct_answer': 1,
                'explanation': 'getElementById retrieves the element with the provided ID.',
                'points': 10,
                'estimated_time_seconds': 40
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which event fires when a form is submitted?',
                'options': ['click', 'load', 'submit', 'change'],
                'correct_answer': 2,
                'explanation': 'The submit event triggers before the form is sent to the server.',
                'points': 10,
                'estimated_time_seconds': 40
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is the result of typeof NaN?',
                'options': ['number', 'NaN', 'undefined', 'object'],
                'correct_answer': 0,
                'explanation': 'NaN is considered a numeric value, so typeof NaN is "number".',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which of the following is how you write a single line comment?',
                'options': ['/* comment */', '// comment', '<!-- comment -->', '# comment'],
                'correct_answer': 1,
                'explanation': 'JavaScript uses // for single-line comments.',
                'points': 10,
                'estimated_time_seconds': 25
            },
            {
                'skill_name': 'JavaScript',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which operator checks for both type and value equality?',
                'options': ['==', '===', '=', '!=='],
                'correct_answer': 1,
                'explanation': '=== performs strict equality comparison.',
                'points': 10,
                'estimated_time_seconds': 35
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
            {
                'skill_name': 'React',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What does React use to pass data into components?',
                'options': ['state', 'props', 'context', 'hooks'],
                'correct_answer': 1,
                'explanation': 'Props are the primary way to pass data from parents to children.',
                'points': 10,
                'estimated_time_seconds': 35
            },
            {
                'skill_name': 'React',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which hook is ideal for running side effects after rendering?',
                'options': ['useState', 'useEffect', 'useMemo', 'useRef'],
                'correct_answer': 1,
                'explanation': 'useEffect runs after render and is used for side effects.',
                'points': 10,
                'estimated_time_seconds': 40
            },
            {
                'skill_name': 'React',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which attribute should be provided when rendering lists of elements?',
                'options': ['id', 'className', 'key', 'style'],
                'correct_answer': 2,
                'explanation': 'key helps React identify which items changed, preventing re-renders.',
                'points': 10,
                'estimated_time_seconds': 30
            },
            {
                'skill_name': 'React',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'What is the function component signature?',
                'options': ['function Component() {}', 'class Component extends React', 'React.createComponent()', 'Component => {}'],
                'correct_answer': 0,
                'explanation': 'Function components are simple functions that return JSX.',
                'points': 10,
                'estimated_time_seconds': 35
            },
            {
                'skill_name': 'React',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Where should you put reusable logic that depends on state?',
                'options': ['render()', 'hooks', 'props', 'context'],
                'correct_answer': 1,
                'explanation': 'Custom hooks (or built-in hooks) keep stateful logic reusable.',
                'points': 10,
                'estimated_time_seconds': 45
            },
            {
                'skill_name': 'React',
                'difficulty': 'BEGINNER',
                'question_type': 'MULTIPLE_CHOICE',
                'question': 'Which method allows you to render multiple elements without extra DOM nodes?',
                'options': ['React.Fragment', 'React.Div', 'React.Fragment()', 'React.timeout'],
                'correct_answer': 0,
                'explanation': 'React.Fragment wraps children without adding nodes to the DOM.',
                'points': 10,
                'estimated_time_seconds': 40
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
