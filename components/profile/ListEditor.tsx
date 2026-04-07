import { Plus, Trash2, Edit3, X, Check } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Field {
  key: string;
  label: string;
  type: "text" | "textarea" | "select" | "checkbox" | "date" | "number";
  placeholder?: string;
  options?: { value: string; label: string }[];
}

interface ListEditorProps<T> {
  title: string;
  items: T[];
  onUpdate: (items: T[]) => void;
  fields: Field[];
  newItemTemplate: T;
  renderItem: (item: T) => React.ReactNode;
}

export default function ListEditor<T extends Record<string, any>>({
  title,
  items,
  onUpdate,
  fields,
  newItemTemplate,
  renderItem
}: ListEditorProps<T>) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editBuffer, setEditBuffer] = useState<T | null>(null);

  const startAdding = () => {
    setEditingIndex(-1);
    setEditBuffer({ ...newItemTemplate });
  };

  const startEditing = (index: number) => {
    setEditingIndex(index);
    setEditBuffer({ ...items[index] });
  };

  const cancelEditing = () => {
    setEditingIndex(null);
    setEditBuffer(null);
  };

  const saveEditing = () => {
    if (editBuffer) {
      if (editingIndex === -1) {
        onUpdate([...items, editBuffer]);
      } else if (editingIndex !== null) {
        const newItems = [...items];
        newItems[editingIndex] = editBuffer;
        onUpdate(newItems);
      }
    }
    cancelEditing();
  };

  const removeItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    onUpdate(newItems);
  };

  const handleFieldChange = (key: string, value: any) => {
    if (editBuffer) {
      setEditBuffer({ ...editBuffer, [key]: value });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h4 className="text-xl font-black text-zinc-900 italic uppercase tracking-tighter">{title}</h4>
        <button
          onClick={startAdding}
          className="flex items-center space-x-2 px-4 py-2 bg-zinc-900 text-white rounded-xl font-black text-[10px] uppercase tracking-widest italic hover:scale-105 transition-all"
        >
          <Plus className="w-3 h-3 text-primary" />
          <span>Add Entry</span>
        </button>
      </div>

      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={index} className="group relative bg-gray-50/50 border border-gray-100 rounded-[32px] p-6 hover:bg-white hover:shadow-xl transition-all">
            {renderItem(item)}
            <div className="absolute top-6 right-6 flex space-x-2 opacity-0 group-hover:opacity-100 transition-all">
              <button onClick={() => startEditing(index)} className="p-2 bg-white shadow-sm border border-gray-100 rounded-xl hover:text-primary transition-colors">
                <Edit3 className="w-4 h-4" />
              </button>
              <button onClick={() => removeItem(index)} className="p-2 bg-white shadow-sm border border-gray-100 rounded-xl hover:text-red-500 transition-colors">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}

        {items.length === 0 && editingIndex === null && (
          <div className="text-center py-10 bg-gray-50/30 border border-dashed border-gray-200 rounded-[32px]">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest italic">No entries yet. Initialize protocol.</p>
          </div>
        )}
      </div>

      <AnimatePresence>
        {editingIndex !== null && editBuffer && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-zinc-950/20 backdrop-blur-sm"
          >
            <div className="bg-white rounded-[40px] shadow-2xl border border-gray-100 w-full max-w-2xl overflow-hidden">
              <div className="p-8 border-b border-gray-50 flex items-center justify-between">
                <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase">{editingIndex === -1 ? 'Add Entry' : 'Edit Entry'}</h3>
                <button onClick={cancelEditing} className="p-2 hover:bg-gray-50 rounded-full transition-colors">
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="p-8 space-y-6 max-h-[70vh] overflow-y-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {fields.map((field) => (
                    <div key={field.key} className={field.type === "textarea" ? "md:col-span-2" : ""}>
                      <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-3">{field.label}</label>
                      {field.type === "textarea" ? (
                        <textarea
                          value={editBuffer[field.key] || ""}
                          onChange={(e) => handleFieldChange(field.key, e.target.value)}
                          placeholder={field.placeholder}
                          className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold h-32 resize-none"
                        />
                      ) : field.type === "select" ? (
                        <select
                          value={editBuffer[field.key] || ""}
                          onChange={(e) => handleFieldChange(field.key, e.target.value)}
                          className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold appearance-none"
                        >
                          {field.options?.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      ) : field.type === "checkbox" ? (
                        <label className="flex items-center space-x-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={!!editBuffer[field.key]}
                            onChange={(e) => handleFieldChange(field.key, e.target.checked)}
                            className="w-5 h-5 rounded-lg border-2 border-gray-200 text-primary focus:ring-0"
                          />
                          <span className="font-bold text-sm text-zinc-900">Current Position / Active</span>
                        </label>
                      ) : (
                        <input
                          type={field.type}
                          value={field.type === "number" ? (editBuffer[field.key] || 0) : (editBuffer[field.key] || "")}
                          onChange={(e) => handleFieldChange(field.key, field.type === "number" ? parseInt(e.target.value) : e.target.value)}
                          placeholder={field.placeholder}
                          className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
              <div className="p-8 bg-gray-50 border-t border-gray-100 flex justify-end space-x-4">
                <button
                  onClick={cancelEditing}
                  className="px-8 py-4 font-black uppercase tracking-widest text-xs text-gray-400 hover:text-zinc-900 transition-colors"
                >
                  Terminate
                </button>
                <button
                  onClick={saveEditing}
                  className="px-10 py-4 bg-zinc-900 text-white rounded-[24px] font-black uppercase tracking-widest text-xs italic shadow-xl hover:scale-105 transition-all flex items-center space-x-2"
                >
                  <Check className="w-4 h-4 text-primary" />
                  <span>Execute Sync</span>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
