"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const CustomCursor = () => {
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const [isHovering, setIsHovering] = useState(false);

    useEffect(() => {
        const mouseMove = (e: MouseEvent) => {
            setMousePosition({
                x: e.clientX,
                y: e.clientY,
            });
        };

        const handleHover = () => setIsHovering(true);
        const handleUnhover = () => setIsHovering(false);

        window.addEventListener("mousemove", mouseMove);
        document.querySelectorAll("a, button").forEach((el) => {
            el.addEventListener("mouseenter", handleHover);
            el.addEventListener("mouseleave", handleUnhover);
        });

        return () => {
            window.removeEventListener("mousemove", mouseMove);
            document.querySelectorAll("a, button").forEach((el) => {
                el.removeEventListener("mouseenter", handleHover);
                el.removeEventListener("mouseleave", handleUnhover);
            });
        };
    }, []);

    const variants = {
        default: {
            x: mousePosition.x - 16,
            y: mousePosition.y - 16,
            transition: { type: "spring", stiffness: 500, damping: 28 },
        },
        hover: {
            x: mousePosition.x - 40,
            y: mousePosition.y - 40,
            scale: 2.5,
            backgroundColor: "rgba(0, 102, 255, 0.15)",
            transition: { type: "spring", stiffness: 500, damping: 28 },
        },
    };

    return (
        <motion.div
            className="fixed top-0 left-0 w-8 h-8 rounded-full border border-primary/30 pointer-events-none z-[9999] hidden lg:block backdrop-blur-[2px]"
            variants={variants}
            animate={isHovering ? "hover" : "default"}
        >
            <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-1 bg-primary rounded-full ${isHovering ? 'opacity-100' : 'opacity-0'}`} />
        </motion.div>
    );
};

export default CustomCursor;
