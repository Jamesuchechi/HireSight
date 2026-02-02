/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./templates/**/*.html",
        "./static/**/*.js",
        "./apps/**/templates/**/*.html",
        "./apps/**/forms.py",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                'primary': '#0066FF',
                'primary-light': '#E6F0FF',
                'primary-dark': '#0052CC',
                'secondary': '#00D4FF',
                'secondary-light': '#E6F9FF',
                'accent': '#FFB800',
                'success': '#00C853',
                'danger': '#FF3B30',
                'warning': '#FF9500',
                'purple': '#9333EA',
            },
            fontFamily: {
                'display': ['Poppins', 'sans-serif'],
                'body': ['Inter', 'sans-serif'],
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-in-out',
                'slide-up': 'slideUp 0.5s ease-out',
                'slide-down': 'slideDown 0.3s ease-out',
                'scale-in': 'scaleIn 0.3s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                slideDown: {
                    '0%': { transform: 'translateY(-20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                scaleIn: {
                    '0%': { transform: 'scale(0.9)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
            }
        }
    },
    plugins: [],
}
