'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import { Moon, Sun, MessageSquare, LogOut, User } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { user, isAuthenticated, logout, darkMode, toggleDarkMode } = useAuthStore();
  const [url, setUrl] = useState('');
  const [isIngesting, setIsIngesting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsIngesting(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.API_URL || 'http://localhost:8000'}/api/v1/documents/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to ingest website');
      }

      const document = await response.json();
      router.push(`/chat?documentId=${document.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsIngesting(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-dark-900 dark:to-dark-950">
        {/* Header */}
        <header className="bg-white/80 dark:bg-dark-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-dark-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-3">
                <MessageSquare className="w-8 h-8 text-primary-500" />
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">RAG Chatbot</h1>
              </div>
              
              <div className="flex items-center space-x-4">
                <button
                  onClick={toggleDarkMode}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors"
                >
                  {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
                
                <div className="flex items-center space-x-2">
                  <User className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{user?.email}</span>
                </div>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Ask Questions About Any Website
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Enter a website URL and start chatting with AI about its content
            </p>
          </div>

          <div className="bg-white dark:bg-dark-800 rounded-2xl shadow-xl p-8">
            <form onSubmit={handleIngest} className="space-y-6">
              <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Website URL
                </label>
                <input
                  type="url"
                  id="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  required
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                />
              </div>

              {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isIngesting}
                className="w-full py-4 px-6 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-300 dark:disabled:bg-primary-700 text-white font-semibold rounded-lg transition-all transform hover:scale-[1.02] disabled:transform-none disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isIngesting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Ingesting Website...</span>
                  </>
                ) : (
                  <span>Start Chatting</span>
                )}
              </button>
            </form>

            <div className="mt-8 pt-8 border-t border-gray-200 dark:border-dark-700">
              <Link
                href="/documents"
                className="text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 font-medium flex items-center justify-center space-x-2"
              >
                <MessageSquare className="w-4 h-4" />
                <span>View My Documents & Conversations</span>
              </Link>
            </div>
          </div>

          {/* Features */}
          <div className="mt-12 grid md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-dark-800 rounded-xl p-6 shadow-lg">
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Web Crawling</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">Automatically crawl and extract content from any website</p>
            </div>

            <div className="bg-white dark:bg-dark-800 rounded-xl p-6 shadow-lg">
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">PDF Support</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">Upload PDF documents and chat about their content</p>
            </div>

            <div className="bg-white dark:bg-dark-800 rounded-xl p-6 shadow-lg">
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">AI-Powered</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">Get accurate answers powered by advanced LLMs</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
