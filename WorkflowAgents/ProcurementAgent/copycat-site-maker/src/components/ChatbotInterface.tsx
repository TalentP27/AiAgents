import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Mic, Paperclip, Download } from 'lucide-react';
import chatbotAvatar from '@/assets/chatbot-avatar.png';
import { procure, downloadCSV } from '../services/procurementService';
import ReactMarkdown from 'react-markdown';

const ChatbotInterface = () => {
  const [message, setMessage] = useState('');
  const [location, setLocation] = useState('');
  const [showProgress, setShowProgress] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<string | null>(null);
  const [csvAvailable, setCsvAvailable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGetStarted = async () => {
    setShowProgress(true);
    setProgress(0);
    setResult(null);
    setCsvAvailable(false);
    setError(null);
    // Progress animation
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + (100 / 30); // 3 seconds = 30 * 100ms
      });
    }, 100);
    try {
      // Use message as product list, and location (or hardcode for now)
      const data = await procure(message, location || 'Paris, France');
      setResult(data.markdown);
      setCsvAvailable(data.csv_available);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setTimeout(() => setShowProgress(false), 3000);
    }
  };

  const handleDownloadCSV = () => {
    downloadCSV();
  };

  return (
    <div className="min-h-screen bg-chatbot-background flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Chatbot Avatar */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-200 via-purple-200 to-purple-300 flex items-center justify-center shadow-lg">
              <img 
                src={chatbotAvatar} 
                alt="KIT Chatbot Avatar" 
                className="w-28 h-28 rounded-full object-cover"
              />
            </div>
            {/* Glow effect */}
            <div className="absolute inset-0 w-32 h-32 rounded-full bg-gradient-to-br from-blue-200 via-purple-200 to-purple-300 opacity-30 blur-xl -z-10"></div>
          </div>
        </div>

        {/* Greeting Messages */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-normal text-foreground mb-2">
            Hi Jean, I'm an AI procurement agent.
          </h1>
          <p className="text-2xl md:text-3xl font-normal text-muted-foreground">
            How can I help you today?
          </p>
        </div>

        {/* Input Section */}
        <div className="flex items-center gap-3 max-w-xl mx-auto mb-4">
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="I need..."
              className="h-14 text-lg pl-4 pr-12 bg-chatbot-input border-border rounded-xl shadow-sm focus:ring-2 focus:ring-chatbot-primary focus:border-transparent"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
              <button className="p-1.5 hover:bg-muted rounded-full transition-colors">
                <Paperclip className="w-5 h-5 text-muted-foreground" />
              </button>
              <button className="p-1.5 hover:bg-muted rounded-full transition-colors">
                <Mic className="w-5 h-5 text-muted-foreground" />
              </button>
            </div>
          </div>
          {/* Optional: Add a location input if you want */}
          {/* <Input value={location} onChange={e => setLocation(e.target.value)} placeholder="Location (city, country)" className="h-14 text-lg pl-4 pr-4 bg-chatbot-input border-border rounded-xl shadow-sm" /> */}
          <Button 
            onClick={handleGetStarted}
            className="h-14 px-8 text-lg font-medium bg-chatbot-primary hover:bg-chatbot-primary-light text-white rounded-xl shadow-sm transition-all duration-200 hover:shadow-md"
            disabled={showProgress || !message}
          >
            Get started
          </Button>
        </div>

        {/* Progress Bar */}
        {showProgress && (
          <div className="mt-8 max-w-xl mx-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Processing...</span>
              <span className="text-sm font-medium text-chatbot-primary animate-pulse">
                {Math.round(progress)}%
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        )}

        {/* Result Section */}
        {result && (
          <div className="mt-8 max-w-xl mx-auto bg-white rounded-xl shadow p-6">
            <h2 className="text-xl font-semibold mb-2">Procurement Results</h2>
            {(() => {
              // Filter to show only the summary and recommendations
              const summaryStart = result.indexOf('### 📊 Data Summary:') !== -1
                ? result.indexOf('### 📊 Data Summary:')
                : result.indexOf('### Data Summary:');
              const displayResult = summaryStart !== -1 ? result.slice(summaryStart) : result;
              return (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{displayResult}</ReactMarkdown>
                </div>
              );
            })()}
          </div>
        )}
        {error && (
          <div className="mt-8 max-w-xl mx-auto text-center text-red-600">{error}</div>
        )}

        {/* Download Section */}
        <div className="mt-4 max-w-xl mx-auto text-center">
          <h2 className="text-2xl font-semibold text-foreground mb-4">
            Download the procurement data
          </h2>
          <Button 
            onClick={handleDownloadCSV}
            className="h-12 px-6 text-base font-medium bg-chatbot-primary hover:bg-chatbot-primary-light text-white rounded-xl shadow-sm transition-all duration-200 hover:shadow-md flex items-center gap-2 mx-auto"
            disabled={!csvAvailable}
          >
            <Download className="w-5 h-5" />
            Download CSV
          </Button>
        </div>

        {/* Optional: Quick actions or suggestions */}
        <div className="flex justify-center mt-8">
          <div className="flex flex-wrap gap-2 justify-center max-w-lg">
            <button className="px-4 py-2 bg-white border border-border rounded-full text-sm text-muted-foreground hover:bg-accent transition-colors">
              Order supplies
            </button>
            <button className="px-4 py-2 bg-white border border-border rounded-full text-sm text-muted-foreground hover:bg-accent transition-colors">
              Track delivery
            </button>
            <button className="px-4 py-2 bg-white border border-border rounded-full text-sm text-muted-foreground hover:bg-accent transition-colors">
              Get support
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatbotInterface;