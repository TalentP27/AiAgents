import Retell from 'retell-sdk';

// Initialize RetellAI client with your API key
const retellClient = new Retell({
  apiKey: 'key_1501adb94f79644ed8f3f9c0fc51', // Your RetellAI API key
});

// Your RetellAI agent ID
const AGENT_ID = 'agent_46b88cf66474b91d090194619b';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatSession {
  chatId: string;
  messages: ChatMessage[];
}

class RetellChatService {
  private static instance: RetellChatService;
  private currentSession: ChatSession | null = null;

  private constructor() {}

  public static getInstance(): RetellChatService {
    if (!RetellChatService.instance) {
      RetellChatService.instance = new RetellChatService();
    }
    return RetellChatService.instance;
  }

  // Start a new chat session
  async startChatSession(): Promise<string> {
    console.log('Starting new RetellAI chat session with agent:', AGENT_ID);
    
    try {
      // Create a new chat session with RetellAI
      const chatResponse = await retellClient.chat.create({
        agent_id: AGENT_ID,
      });

      console.log('Chat session created successfully:', chatResponse.chat_id);

      this.currentSession = {
        chatId: chatResponse.chat_id,
        messages: [],
      };

      return chatResponse.chat_id;
    } catch (error: any) {
      console.error('Error starting chat session:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        response: error.response
      });
      
      // Provide more specific error information
      if (error.status === 401) {
        throw new Error('Authentication failed - please check your API key');
      } else if (error.status === 404) {
        throw new Error('Agent not found - please check your agent ID');
      } else {
        throw new Error(`Failed to start chat session: ${error.message || 'Unknown error'}`);
      }
    }
  }

  // Send a message and get response from RetellAI
  async sendMessage(userMessage: string): Promise<string> {
    if (!this.currentSession) {
      console.log('No active session, starting new session...');
      await this.startChatSession();
    }

    console.log('Sending message to RetellAI chat completion API...');
    console.log('Chat ID:', this.currentSession!.chatId);
    console.log('User message:', userMessage);

    try {
      // Send message to RetellAI chat completion API
      const response = await retellClient.chat.createChatCompletion({
        chat_id: this.currentSession!.chatId,
        content: userMessage,
      });

      console.log('Raw API response:', response);

      // Extract the assistant's response from the messages array
      if (response.messages && Array.isArray(response.messages) && response.messages.length > 0) {
        const latestMessage = response.messages[response.messages.length - 1];
        const assistantMessage = latestMessage.content || "I'm here to help with your onboarding!";
        
        console.log('Extracted assistant message:', assistantMessage);

        // Update local session history
        this.currentSession!.messages.push(
          { role: 'user', content: userMessage },
          { role: 'assistant', content: assistantMessage }
        );

        return assistantMessage;
      } else {
        console.warn('No messages in response or invalid response format');
        return "I received your message! How can I help you with your RetailChain onboarding?";
      }
    } catch (error: any) {
      console.error('Error sending message to RetellAI:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        response: error.response
      });
      
      // More specific error handling
      if (error.status === 401) {
        return "I'm having authentication issues. Please try again in a moment.";
      } else if (error.status === 429) {
        return "I'm experiencing high traffic right now. Please wait a moment and try again.";
      } else if (error.status >= 500) {
        return "Our servers are temporarily unavailable. Please try again shortly.";
      } else {
        // Fallback response if API fails
        return "I apologize, but I'm having trouble connecting to our systems right now. Please try again in a moment, or feel free to ask me about RetailChain's onboarding process.";
      }
    }
  }

  // End the current chat session
  async endChatSession(): Promise<void> {
    if (!this.currentSession) return;

    // For now, just clean up the local session
    // RetellAI will automatically close inactive chats based on timeout settings
    this.currentSession = null;
    console.log('Chat session ended locally');
  }

  // Get current session info
  getCurrentSession(): ChatSession | null {
    return this.currentSession;
  }

  // Get chat history
  getChatHistory(): ChatMessage[] {
    return this.currentSession?.messages || [];
  }
}

export default RetellChatService; 