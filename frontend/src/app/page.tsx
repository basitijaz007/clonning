"use client";

import React, { useState, useRef } from "react";
import {
  Mic2,
  Upload,
  Play,
  Download,
  Loader2,
  Volume2,
  Sparkles,
  Waves,
  Globe
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Client } from "@gradio/client";

export default function VoiceClonePage() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("en");
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const generateVoice = async () => {
    if (!text || !file) {
      setError("Please provide both text and a reference audio file.");
      return;
    }

    setIsGenerating(true);
    setError(null);
    setAudioUrl(null);

    try {
      // NOTE: User will need to replace this with their Hugging Face Space URL
      // Example: 'username/space-name'
      const client = await Client.connect("basitijaz/voice-clonning-xtts");
      const result = await client.predict("/predict", {
        text: text,
        audio_file: file,
        language: language
      }) as any;

      if (result.data && result.data[0]) {
        setAudioUrl(result.data[0].url);
      } else if (result.data && result.data[1]) {
        setError(result.data[1]);
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to connect to AI server. Please check your Space visibility.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <main className="min-h-screen p-4 md:p-8 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-0 left-0 w-full h-full -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/10 blur-[120px] rounded-full" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-4xl glass p-8 md:p-12 animate-glow"
      >
        <header className="mb-12 text-center">
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 text-blue-400 text-sm font-medium mb-4"
          >
            <Sparkles className="w-4 h-4" />
            AI Voice Cloning Reality
          </motion.div>
          <h1 className="text-4xl md:text-6xl font-bold mb-4 gradient-text">
            Clone Any Voice <br /> Instantly
          </h1>
          <p className="text-zinc-400 text-lg max-w-xl mx-auto">
            Experience high-quality voice cloning powered by XTTS-v2.
            Upload a sample and hear the magic.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left Column: Inputs */}
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                <Mic2 className="w-4 h-4" /> Reference Voice Sample
              </label>
              <div
                onClick={() => fileInputRef.current?.click()}
                className={`h-32 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-all ${file ? 'border-blue-500/50 bg-blue-500/10' : 'border-zinc-700 hover:border-zinc-500 bg-white/5'
                  }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                  accept="audio/*"
                />
                {file ? (
                  <div className="text-center">
                    <Waves className="w-8 h-8 mx-auto text-blue-400 mb-2 animate-pulse" />
                    <p className="text-sm text-blue-400 font-medium truncate max-w-[200px]">
                      {file.name}
                    </p>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-zinc-500 mb-2" />
                    <p className="text-sm text-zinc-400">Click to upload .wav or .mp3</p>
                  </>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                <Globe className="w-4 h-4" /> Target Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-white/5 border border-zinc-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500/50 transition-all text-white appearance-none"
              >
                <option value="en">English (US)</option>
                <option value="ru">Russian</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
                <option value="tr">Turkish</option>
                <option value="ar">Arabic</option>
                <option value="zh-cn">Chinese</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
              </select>
            </div>
          </div>

          {/* Right Column: Text & Action */}
          <div className="flex flex-col">
            <div className="space-y-2 flex-grow">
              <label className="text-sm font-medium text-zinc-300">Script Content</label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="What should the cloned voice say?"
                className="w-full h-[180px] md:h-full min-h-[180px] bg-white/5 border border-zinc-700 rounded-2xl p-4 outline-none focus:border-blue-500/50 transition-all text-white resize-none"
              />
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-col items-center gap-4">
          <button
            onClick={generateVoice}
            disabled={isGenerating || !text || !file}
            className="group relative w-full md:w-auto min-w-[240px] px-8 py-4 bg-white text-black font-bold rounded-full overflow-hidden transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
          >
            <div className="relative z-10 flex items-center justify-center gap-2">
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating Magic...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Clone Now
                </>
              )}
            </div>
            <div className="absolute inset-0 bg-blue-400 translate-y-full group-hover:translate-y-0 transition-transform" />
          </button>

          {error && (
            <p className="text-red-400 text-sm font-medium animate-bounce">{error}</p>
          )}
        </div>

        {/* Result Area */}
        <AnimatePresence>
          {audioUrl && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="mt-12 p-6 rounded-3xl bg-blue-500/5 border border-blue-500/20 flex flex-col md:flex-row items-center gap-6"
            >
              <div className="w-16 h-16 rounded-2xl bg-blue-500 flex items-center justify-center flex-shrink-0 animate-pulse">
                <Volume2 className="w-8 h-8 text-white" />
              </div>
              <div className="flex-grow text-center md:text-left">
                <h3 className="text-xl font-bold text-white mb-1">Cloning Successful!</h3>
                <p className="text-zinc-400 text-sm">Your custom audio is ready for preview and download.</p>
              </div>
              <div className="flex gap-3">
                <audio src={audioUrl} controls className="hidden" id="audio-result" />
                <button
                  onClick={() => (document.getElementById('audio-result') as HTMLAudioElement).play()}
                  className="p-4 rounded-2xl bg-white/10 hover:bg-white/20 transition-all text-white"
                >
                  <Play className="w-6 h-6" />
                </button>
                <a
                  href={audioUrl}
                  download="cloned_voice.wav"
                  className="p-4 rounded-2xl bg-blue-500 hover:bg-blue-600 transition-all text-white"
                >
                  <Download className="w-6 h-6" />
                </a>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <footer className="mt-8 text-zinc-500 text-sm">
        Powered by Coqui XTTS-v2 & Hugging Face • Developed with ❤️
      </footer>
    </main>
  );
}
