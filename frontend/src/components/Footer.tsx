import React from 'react';
import { Mail, Phone, MapPin, Facebook, Twitter, Linkedin, Github } from 'lucide-react';
import Logo from './Logo';

export default function Footer() {
    return (
        <footer className="footer">
            <style>{`
        .footer {
          background: linear-gradient(135deg, #0A0E14 0%, #1a1d23 100%);
          color: #ffffff;
          padding: 4rem 2rem 2rem;
          margin-top: auto;
          position: relative;
        }

        .footer::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 1px;
          background: linear-gradient(90deg, transparent, #0066FF, transparent);
        }

        .footer-content {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 3rem;
        }

        .footer-section h3 {
          color: #ffffff;
          font-size: 1.25rem;
          font-weight: 700;
          margin-bottom: 1.5rem;
          font-family: 'Clash Display', sans-serif;
        }

        .footer-section p {
          color: #9ca3af;
          line-height: 1.6;
          margin-bottom: 1rem;
        }

        .footer-links {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .footer-links li {
          margin-bottom: 0.75rem;
        }

        .footer-links a {
          color: #9ca3af;
          text-decoration: none;
          transition: all 0.2s ease;
          display: inline-block;
        }

        .footer-links a:hover {
          color: #0066FF;
          transform: translateX(4px);
        }

        .contact-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1rem;
          color: #9ca3af;
        }

        .contact-item svg {
          color: #0066FF;
          flex-shrink: 0;
        }

        .social-links {
          display: flex;
          gap: 1rem;
          margin-top: 1.5rem;
        }

        .social-link {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #9ca3af;
          text-decoration: none;
          transition: all 0.2s ease;
        }

        .social-link:hover {
          background: #0066FF;
          color: white;
          transform: translateY(-2px);
        }

        .footer-bottom {
          margin-top: 3rem;
          padding-top: 2rem;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          text-align: center;
          color: #6b7280;
        }

        .footer-bottom-content {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .footer-copyright {
          font-size: 0.9rem;
        }

        .footer-legal {
          display: flex;
          gap: 2rem;
          flex-wrap: wrap;
        }

        .footer-legal a {
          color: #6b7280;
          text-decoration: none;
          font-size: 0.9rem;
          transition: color 0.2s ease;
        }

        .footer-legal a:hover {
          color: #0066FF;
        }

        @media (max-width: 768px) {
          .footer {
            padding: 3rem 1rem 2rem;
          }

          .footer-content {
            grid-template-columns: 1fr;
            gap: 2rem;
          }

          .footer-bottom-content {
            flex-direction: column;
            text-align: center;
            gap: 1.5rem;
          }

          .footer-legal {
            justify-content: center;
          }
        }
      `}</style>

            <div className="footer-content">
                <div className="footer-section">
                    <Logo variant="white" size="medium" showText={true} />
                    <p>
                        Revolutionizing recruitment with AI-powered resume parsing and semantic matching.
                        Find the perfect candidates faster than ever before.
                    </p>
                    <div className="social-links">
                        <a href="#" className="social-link" aria-label="Facebook">
                            <Facebook size={20} />
                        </a>
                        <a href="#" className="social-link" aria-label="Twitter">
                            <Twitter size={20} />
                        </a>
                        <a href="#" className="social-link" aria-label="LinkedIn">
                            <Linkedin size={20} />
                        </a>
                        <a href="#" className="social-link" aria-label="GitHub">
                            <Github size={20} />
                        </a>
                    </div>
                </div>

                <div className="footer-section">
                    <h3>Product</h3>
                    <ul className="footer-links">
                        <li><a href="#">Resume Parsing</a></li>
                        <li><a href="#">Semantic Matching</a></li>
                        <li><a href="#">Analytics Dashboard</a></li>
                        <li><a href="#">API Integration</a></li>
                        <li><a href="#">Enterprise Solutions</a></li>
                    </ul>
                </div>

                <div className="footer-section">
                    <h3>Company</h3>
                    <ul className="footer-links">
                        <li><a href="#">About Us</a></li>
                        <li><a href="#">Careers</a></li>
                        <li><a href="#">Blog</a></li>
                        <li><a href="#">Press Kit</a></li>
                        <li><a href="#">Contact</a></li>
                    </ul>
                </div>

                <div className="footer-section">
                    <h3>Support</h3>
                    <ul className="footer-links">
                        <li><a href="#">Help Center</a></li>
                        <li><a href="#">Documentation</a></li>
                        <li><a href="#">Community</a></li>
                        <li><a href="#">Status</a></li>
                    </ul>
                    <div className="contact-item">
                        <Mail size={18} />
                        <span>support@hiresight.com</span>
                    </div>
                    <div className="contact-item">
                        <Phone size={18} />
                        <span>+1 (555) 123-4567</span>
                    </div>
                </div>
            </div>

            <div className="footer-bottom">
                <div className="footer-bottom-content">
                    <div className="footer-copyright">
                        © 2024 HireSight. All rights reserved.
                    </div>
                    <div className="footer-legal">
                        <a href="#">Privacy Policy</a>
                        <a href="#">Terms of Service</a>
                        <a href="#">Cookie Policy</a>
                    </div>
                </div>
            </div>
        </footer>
    );
}