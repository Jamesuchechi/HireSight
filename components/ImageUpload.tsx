"use client";

import { useState, useRef } from "react";
import { Upload, X, Loader2, Camera, Image as ImageIcon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { createClient } from "@/lib/supabase/client";

interface ImageUploadProps {
    uid: string;
    url: string | null;
    onUpload: (url: string) => void;
    label: string;
    type: "avatar" | "cover";
}

export default function ImageUpload({ uid, url, onUpload, label, type }: ImageUploadProps) {
    const supabase = createClient();
    const [uploading, setUploading] = useState(false);
    const [preview, setPreview] = useState<string | null>(url);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        try {
            setUploading(true);

            if (!event.target.files || event.target.files.length === 0) {
                throw new Error("You must select an image to upload.");
            }

            const file = event.target.files[0];
            const fileExt = file.name.split(".").pop();
            const filePath = `${uid}/${type}-${Math.random()}.${fileExt}`;

            // 1. Create a local preview
            const objectUrl = URL.createObjectURL(file);
            setPreview(objectUrl);

            // 2. Upload to Supabase Storage
            const { error: uploadError } = await supabase.storage
                .from("profile-assets")
                .upload(filePath, file);

            if (uploadError) {
                throw uploadError;
            }

            // 3. Get Public URL
            const { data } = supabase.storage
                .from("profile-assets")
                .getPublicUrl(filePath);

            onUpload(data.publicUrl);
        } catch (error: any) {
            alert(error.message);
        } finally {
            setUploading(false);
        }
    };

    const isAvatar = type === "avatar";

    return (
        <div className="space-y-4 w-full">
            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest leading-none">
                {label}
            </label>
            
            <div 
                onClick={() => fileInputRef.current?.click()}
                className={`relative group cursor-pointer overflow-hidden border-2 border-dashed border-gray-100 hover:border-primary/30 transition-all bg-gray-50/50 ${
                    isAvatar ? "w-40 h-40 rounded-[48px]" : "w-full h-48 rounded-[32px]"
                }`}
            >
                {/* Current Image / Preview */}
                {preview ? (
                    <img 
                        src={preview} 
                        alt={label} 
                        className="w-full h-full object-cover transition-transform group-hover:scale-110 duration-700" 
                    />
                ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center space-y-3 text-gray-400">
                        {isAvatar ? <Camera className="w-8 h-8" /> : <ImageIcon className="w-10 h-10" />}
                        <span className="text-[10px] font-black uppercase tracking-widest">Select File</span>
                    </div>
                )}

                {/* Overlay on Hover */}
                <div className="absolute inset-0 bg-zinc-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-sm">
                    <div className="flex flex-col items-center space-y-2 text-white">
                        <Upload className="w-6 h-6" />
                        <span className="text-[10px] font-black uppercase tracking-widest whitespace-nowrap">Replace {type}</span>
                    </div>
                </div>

                {/* Loading State */}
                <AnimatePresence>
                    {uploading && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-white/80 backdrop-blur-md flex flex-col items-center justify-center z-10"
                        >
                            <Loader2 className="w-8 h-8 text-primary animate-spin mb-2" />
                            <span className="text-[10px] font-black text-primary uppercase tracking-widest">Uploading...</span>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <input
                type="file"
                className="hidden"
                ref={fileInputRef}
                onChange={handleUpload}
                accept="image/*"
                disabled={uploading}
            />
            
            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest leading-none">
                Max size: 5MB • Formats: JPG, PNG, WEBP
            </p>
        </div>
    );
}
