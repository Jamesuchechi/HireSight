"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import Underline from "@tiptap/extension-underline";
import Placeholder from "@tiptap/extension-placeholder";
import { 
    Bold, Italic, List, ListOrdered, LinkIcon, 
    Heading1, Heading2, Quote, Undo, Redo, 
    Underline as UnderlineIcon 
} from "lucide-react";

interface RichTextEditorProps {
    content: string;
    onChange: (content: string) => void;
    placeholder?: string;
}

const MenuButton = ({ 
    onClick, 
    isActive = false, 
    children 
}: { 
    onClick: () => void; 
    isActive?: boolean; 
    children: React.ReactNode 
}) => (
    <button
        type="button"
        onClick={onClick}
        className={`p-2 rounded-lg transition-all ${
            isActive 
                ? "bg-primary text-white shadow-lg shadow-primary/20" 
                : "text-gray-400 hover:bg-gray-100 hover:text-zinc-900"
        }`}
    >
        {children}
    </button>
);

export default function RichTextEditor({ content, onChange, placeholder }: RichTextEditorProps) {
    const editor = useEditor({
        extensions: [
            StarterKit,
            Underline,
            Link.configure({
                openOnClick: false,
            }),
            Placeholder.configure({
                placeholder: placeholder || "Write something amazing...",
            }),
        ],
        content: content,
        immediatelyRender: false,
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML());
        },
        editorProps: {
            attributes: {
                class: "prose prose-sm max-w-none focus:outline-none min-h-[200px] p-6 font-body text-zinc-800 leading-relaxed",
            },
        },
    });

    if (!editor) return null;

    return (
        <div className="w-full border border-gray-100 rounded-[24px] bg-white overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-1 p-2 border-b border-gray-50 bg-gray-50/50">
                <MenuButton 
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    isActive={editor.isActive("bold")}
                >
                    <Bold className="w-4 h-4" />
                </MenuButton>
                <MenuButton 
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    isActive={editor.isActive("italic")}
                >
                    <Italic className="w-4 h-4" />
                </MenuButton>
                <MenuButton 
                    onClick={() => editor.chain().focus().toggleUnderline().run()}
                    isActive={editor.isActive("underline")}
                >
                    <UnderlineIcon className="w-4 h-4" />
                </MenuButton>
                
                <div className="w-px h-6 bg-gray-200 mx-1" />

                <MenuButton 
                    onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                    isActive={editor.isActive("heading", { level: 1 })}
                >
                    <Heading1 className="w-4 h-4" />
                </MenuButton>
                <MenuButton 
                    onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                    isActive={editor.isActive("heading", { level: 2 })}
                >
                    <Heading2 className="w-4 h-4" />
                </MenuButton>

                <div className="w-px h-6 bg-gray-200 mx-1" />

                <MenuButton 
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    isActive={editor.isActive("bulletList")}
                >
                    <List className="w-4 h-4" />
                </MenuButton>
                <MenuButton 
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    isActive={editor.isActive("orderedList")}
                >
                    <ListOrdered className="w-4 h-4" />
                </MenuButton>
                <MenuButton 
                    onClick={() => editor.chain().focus().toggleBlockquote().run()}
                    isActive={editor.isActive("blockquote")}
                >
                    <Quote className="w-4 h-4" />
                </MenuButton>

                <div className="ml-auto flex items-center gap-1">
                    <MenuButton onClick={() => editor.chain().focus().undo().run()}>
                        <Undo className="w-4 h-4" />
                    </MenuButton>
                    <MenuButton onClick={() => editor.chain().focus().redo().run()}>
                        <Redo className="w-4 h-4" />
                    </MenuButton>
                </div>
            </div>

            {/* Editor Content */}
            <EditorContent editor={editor} />
        </div>
    );
}
