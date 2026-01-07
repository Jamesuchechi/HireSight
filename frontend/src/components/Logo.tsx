import React from 'react';

type LogoProps = {
    size?: 'small' | 'medium' | 'large';
    variant?: 'default' | 'white' | 'dark';
    animated?: boolean;
    showText?: boolean;
    className?: string;
};

export default function Logo({
    size = 'medium',
    variant = 'default',
    animated = false,
    showText = true,
    className = ''
}: LogoProps) {
    const sizeClasses = {
        small: 'logo-small',
        medium: 'logo-medium',
        large: 'logo-large'
    };

    const variantClasses = {
        default: 'logo-default',
        white: 'logo-white',
        dark: 'logo-dark'
    };

    return (
        <div className={`logo ${sizeClasses[size]} ${variantClasses[variant]} ${animated ? 'logo-animated' : ''} ${className}`}>
            <style>{`
        .logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-family: 'Clash Display', sans-serif;
          font-weight: 700;
          text-decoration: none;
          transition: all 0.3s ease;
          position: relative;
        }

        .logo:hover {
          transform: scale(1.02);
        }

        .logo-small {
          font-size: 1rem;
        }

        .logo-small .logo-icon {
          width: 28px;
          height: 28px;
        }

        .logo-medium {
          font-size: 1.25rem;
        }

        .logo-medium .logo-icon {
          width: 40px;
          height: 40px;
        }

        .logo-large {
          font-size: 2rem;
        }

        .logo-large .logo-icon {
          width: 56px;
          height: 56px;
        }

        .logo-icon {
          position: relative;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: inherit;
          font-weight: 800;
          color: white;
          overflow: hidden;
          transition: all 0.3s ease;
          box-shadow: 0 4px 16px rgba(0, 102, 255, 0.3);
        }

        .logo-default .logo-icon {
          background: linear-gradient(135deg, #0066FF 0%, #00D4FF 50%, #FFB800 100%);
        }

        .logo-white .logo-icon {
          background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
          color: #0066FF;
          box-shadow: 0 4px 16px rgba(255, 255, 255, 0.3);
        }

        .logo-dark .logo-icon {
          background: linear-gradient(135deg, #0A0E14 0%, #1a1d23 100%);
          box-shadow: 0 4px 16px rgba(10, 14, 20, 0.5);
        }

        .logo-icon::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
          transition: left 0.5s ease;
        }

        .logo:hover .logo-icon::before {
          left: 100%;
        }

        .logo-animated .logo-icon {
          animation: logoPulse 2s infinite ease-in-out;
        }

        @keyframes logoPulse {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 4px 16px rgba(0, 102, 255, 0.3);
          }
          50% {
            transform: scale(1.05);
            box-shadow: 0 8px 24px rgba(0, 102, 255, 0.5);
          }
        }

        .logo-text {
          background: linear-gradient(135deg, #0A0E14 0%, #0066FF 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: -0.02em;
          position: relative;
        }

        .logo-white .logo-text {
          background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .logo-dark .logo-text {
          background: linear-gradient(135deg, #FFFFFF 0%, #9ca3af 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .logo-animated .logo-text {
          animation: textGlow 3s infinite ease-in-out;
        }

        @keyframes textGlow {
          0%, 100% {
            filter: drop-shadow(0 0 4px rgba(0, 102, 255, 0.3));
          }
          50% {
            filter: drop-shadow(0 0 8px rgba(0, 102, 255, 0.6));
          }
        }

        /* Icon content with better typography */
        .logo-icon::after {
          content: 'H';
          position: relative;
          z-index: 1;
          font-weight: 900;
          font-style: italic;
          transform: rotate(-5deg);
          display: inline-block;
        }

        .logo-small .logo-icon::after {
          font-size: 1.2em;
        }

        .logo-medium .logo-icon::after {
          font-size: 1.1em;
        }

        .logo-large .logo-icon::after {
          font-size: 1em;
        }

        /* Subtle background pattern */
        .logo-icon {
          background-image:
            radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
        }

        .logo-white .logo-icon {
          background-image:
            radial-gradient(circle at 25% 25%, rgba(0, 102, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(0, 102, 255, 0.1) 0%, transparent 50%);
        }

        .logo-dark .logo-icon {
          background-image:
            radial-gradient(circle at 25% 25%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(0, 212, 255, 0.1) 0%, transparent 50%);
        }
      `}</style>

            <div className="logo-icon"></div>
            {showText && <span className="logo-text">HireSight</span>}
        </div>
    );
}