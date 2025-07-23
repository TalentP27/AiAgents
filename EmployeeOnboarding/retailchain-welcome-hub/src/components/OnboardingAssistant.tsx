
import React, { useState, useEffect, useRef } from 'react';
import { Phone, MessageCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import RetellChatService from '@/services/retellChatService';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

type OnboardingState = 'initial' | 'call' | 'chat';

const OnboardingAssistant = () => {
  const [currentState, setCurrentState] = useState<OnboardingState>('initial');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [retellChatService] = useState(() => RetellChatService.getInstance());
  const [nextMessageId, setNextMessageId] = useState(1);
  const [hasStarted, setHasStarted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages update
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Focus input when chat opens
  useEffect(() => {
    if (currentState === 'chat' && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 500); // Delay to ensure animation completes
    }
  }, [currentState]);

  // Start conversation and get initial message from RetellAI
  const startConversation = async () => {
    setIsLoading(true);
    setHasStarted(true);
    
    try {
      console.log('Getting initial message from RetellAI...');
      
      // Send an initial greeting to trigger the agent's welcome message
      const initialResponse = await retellChatService.sendMessage("Hello");
      
      const welcomeMessage: Message = {
        id: nextMessageId,
        text: initialResponse,
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages([welcomeMessage]);
      setNextMessageId(prev => prev + 1);
      
      // Focus input after getting initial message
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
      
    } catch (error) {
      console.error('Failed to get initial message:', error);
      
      // Fallback welcome message
      const fallbackMessage: Message = {
        id: nextMessageId,
        text: "Welcome to RetailChain! I'm here to help you with your onboarding. How can I assist you?",
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages([fallbackMessage]);
      setNextMessageId(prev => prev + 1);
    } finally {
      setIsLoading(false);
    }
  };

  const startCall = () => {
    setIsAnimating(true);
    setTimeout(() => {
      setCurrentState('call');
      setIsAnimating(false);
    }, 300);
  };

  const startChat = async () => {
    setIsAnimating(true);
    try {
      // Initialize RetellAI chat session
      await retellChatService.startChatSession();
      setTimeout(() => {
        setCurrentState('chat');
        setIsAnimating(false);
      }, 300);
    } catch (error) {
      console.error('Failed to start chat session:', error);
      setTimeout(() => {
        setCurrentState('chat');
        setIsAnimating(false);
      }, 300);
    }
  };

  const returnToInitial = async () => {
    setIsAnimating(true);
    // End RetellAI chat session
    try {
      await retellChatService.endChatSession();
    } catch (error) {
      console.error('Failed to end chat session:', error);
    }
    
    // Reset conversation state
    setMessages([]);
    setHasStarted(false);
    setNextMessageId(1);
    setInputMessage('');
    
    setTimeout(() => {
      setCurrentState('initial');
      setIsAnimating(false);
    }, 300);
  };

  const sendMessage = async () => {
    if (inputMessage.trim() && !isLoading) {
      const userMessage = inputMessage.trim();
      const userMessageId = nextMessageId;
      const assistantMessageId = nextMessageId + 1;
      
      const newMessage: Message = {
        id: userMessageId,
        text: userMessage,
        sender: 'user',
        timestamp: new Date()
      };
      
      // Add user message immediately
      setMessages(prev => [...prev, newMessage]);
      setInputMessage('');
      setIsLoading(true);
      setNextMessageId(prev => prev + 2); // Reserve IDs for both user and assistant messages
      
      // Keep focus on input field
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
      
      try {
        console.log('Sending message to RetellAI:', userMessage);
        
        // Send message to RetellAI and get response
        const assistantResponse = await retellChatService.sendMessage(userMessage);
        
        console.log('Received response from RetellAI:', assistantResponse);
        
        if (assistantResponse && assistantResponse.trim()) {
          const responseMessage: Message = {
            id: assistantMessageId,
            text: assistantResponse,
            sender: 'assistant',
            timestamp: new Date()
          };
          
          setMessages(prev => [...prev, responseMessage]);
        } else {
          // Handle empty response
          const fallbackMessage: Message = {
            id: assistantMessageId,
            text: "I'm here to help! Could you please rephrase your question?",
            sender: 'assistant',
            timestamp: new Date()
          };
          
          setMessages(prev => [...prev, fallbackMessage]);
        }
      } catch (error) {
        console.error('Failed to send message:', error);
        
        // Fallback response
        const errorMessage: Message = {
          id: assistantMessageId,
          text: "I apologize, but I'm having trouble connecting right now. Please try again in a moment.",
          sender: 'assistant',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
        // Ensure focus returns to input after loading completes
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className={`w-full max-w-4xl transition-all duration-300 ${isAnimating ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`}>
        
        {/* Initial State - Main Options */}
        {currentState === 'initial' && (
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-black mb-4">
                Welcome to <span className="text-[#E10600]">RetailChain</span>
              </h1>
              <p className="text-gray-600 text-lg">
                Let's get you started with our onboarding process. Choose how you'd like to begin:
              </p>
            </div>
            
            <div className="flex flex-col md:flex-row gap-6 justify-center max-w-2xl mx-auto">
              <Button
                onClick={startCall}
                className="bg-[#E10600] hover:bg-[#C10500] text-white h-20 text-lg font-semibold rounded-xl transition-all duration-200 hover:scale-105 shadow-lg"
                size="lg"
              >
                <Phone className="mr-3 h-6 w-6" />
                Start Onboarding via Call
              </Button>
              
              <Button
                onClick={startChat}
                className="bg-[#E10600] hover:bg-[#C10500] text-white h-20 text-lg font-semibold rounded-xl transition-all duration-200 hover:scale-105 shadow-lg"
                size="lg"
              >
                <MessageCircle className="mr-3 h-6 w-6" />
                Start Onboarding via Chat
              </Button>
            </div>
          </div>
        )}

        {/* Call State */}
        {currentState === 'call' && (
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="mb-8">
              <div className="animate-pulse mb-6">
                <Phone className="h-16 w-16 text-[#E10600] mx-auto animate-bounce" />
              </div>
              <h2 className="text-3xl font-bold text-black mb-4">
                Starting your call...
              </h2>
              <p className="text-gray-600 text-lg mb-2">
                Please keep your phone nearby
              </p>
              <p className="text-sm text-gray-500">
                Our onboarding specialist will contact you within the next 2 minutes
              </p>
            </div>
            
            <div className="flex items-center justify-center space-x-4 mb-8">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-[#E10600] rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-[#E10600] rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-[#E10600] rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
            
            <Button
              onClick={returnToInitial}
              variant="outline"
              className="border-[#E10600] text-[#E10600] hover:bg-[#E10600] hover:text-white transition-all duration-200"
            >
              <X className="mr-2 h-4 w-4" />
              Cancel Call
            </Button>
          </div>
        )}

        {/* Chat State */}
        {currentState === 'chat' && (
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            {/* Chat Header */}
            <div className="bg-[#E10600] text-white p-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">RetailChain Support</h2>
                <p className="text-red-100 text-sm">We're here to help with your onboarding</p>
              </div>
              <Button
                onClick={returnToInitial}
                variant="ghost"
                size="sm"
                className="text-white hover:bg-red-700"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Messages Area */}
            <div className="h-96 overflow-y-auto p-4 space-y-4">
              {/* Start button when conversation hasn't started */}
              {!hasStarted && messages.length === 0 && !isLoading && (
                <div className="flex flex-col items-center justify-center h-full">
                  <div className="text-center mb-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                      Ready to start your onboarding?
                    </h3>
                    <p className="text-gray-600 text-sm">
                      Click the button below to begin chatting with our AI assistant
                    </p>
                  </div>
                  <Button
                    onClick={startConversation}
                    className="bg-[#E10600] hover:bg-[#C10500] text-white px-8 py-3 text-lg font-semibold rounded-xl transition-all duration-200 hover:scale-105 shadow-lg"
                    size="lg"
                  >
                    <MessageCircle className="mr-2 h-5 w-5" />
                    Start Conversation
                  </Button>
                </div>
              )}

              {/* Messages */}
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                      message.sender === 'user'
                        ? 'bg-[#E10600] text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="text-sm">{message.text}</p>
                    <p className={`text-xs mt-1 ${
                      message.sender === 'user' ? 'text-red-100' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </p>
                  </div>
                </div>
              ))}
              
              {/* Loading indicator when AI is thinking */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-2xl bg-gray-100 text-gray-800">
                    <div className="flex items-center space-x-1">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                      <span className="text-xs text-gray-500 ml-2">
                        {hasStarted ? 'AI is thinking...' : 'Starting conversation...'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
            
            {/* Input Area - Only show when conversation has started */}
            {hasStarted && (
              <div className="p-4 border-t border-gray-200">
                <div className="flex space-x-2">
                  <Input
                    ref={inputRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={isLoading ? "AI is thinking..." : "Ask me anything about your onboarding..."}
                    className="flex-1 border-gray-300 focus:border-[#E10600] focus:ring-[#E10600]"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={sendMessage}
                    className="bg-[#E10600] hover:bg-[#C10500] text-white px-6"
                    disabled={isLoading || !inputMessage.trim()}
                  >
                    {isLoading ? "..." : "Send"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OnboardingAssistant;
