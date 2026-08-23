'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Send,
  Loader2,
  FileText,
  Sparkles,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  MoreVertical,
  Trash2,
  Edit,
  Plus,
  MessageSquare,
  X,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Flag,
  ClipboardList,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { ChatSession, ChatMessage, Tender } from '../types';
import { format, formatDistanceToNow } from 'date-fns';
import {
  Button,
} from '../components/ui/button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../components/ui/card';
import {
  Input,
} from '../components/ui/input';
import {
  Textarea,
} from '../components/ui/textarea';
import {
  Badge,
} from '../components/ui/badge';
import {
  ScrollArea,
} from '../components/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui/tabs';
import {
  Skeleton,
} from '../components/ui/skeleton';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../components/ui/tooltip';
import { Separator } from '../components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { cn } from '../utils/cn';

const SUGGESTED_QUESTIONS = [
  'What are the key requirements for this tender?',
  'Summarize the evaluation criteria',
  'What are the submission deadlines?',
  'Identify potential compliance risks',
  'Suggest a winning strategy for this proposal',
  'What documents do I need to prepare?',
];

export function ChatPage() {
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [newSessionTenderId, setNewSessionTenderId] = useState('');
  const [messageInput, setMessageInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showNewSessionDialog, setShowNewSessionDialog] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState('');

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['chat-sessions'],
    queryFn: () => apiClient.listChatSessions(),
  });

  const { data: tenders } = useQuery({
    queryKey: ['tenders-for-chat'],
    queryFn: () => apiClient.listTenders({ limit: 100 }),
  });

  const activeSession = sessions?.find(s => s.id === activeSessionId) || null;

  const { data: messages, isLoading: messagesLoading } = useQuery({
    queryKey: ['chat-messages', activeSessionId],
    queryFn: () => apiClient.getChatMessages(activeSessionId!),
    enabled: !!activeSessionId,
  });

  const createSessionMutation = useMutation({
    mutationFn: (tenderId: string) => apiClient.createChatSession(tenderId),
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
      setActiveSessionId(session.id);
      setShowNewSessionDialog(false);
      setNewSessionTenderId('');
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) =>
      apiClient.sendChatMessage(sessionId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', activeSessionId] });
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => apiClient.deleteChatSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
      if (activeSessionId === activeSessionId) {
        setActiveSessionId(null);
      }
    },
  });

  const updateMessageMutation = useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) =>
      apiClient.updateChatMessage(id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', activeSessionId] });
      setEditingMessageId(null);
    },
  });

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSendMessage = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!messageInput.trim() || !activeSessionId || isTyping) return;

    const content = messageInput.trim();
    setMessageInput('');
    setIsTyping(true);
    sendMessageMutation.mutate({ sessionId: activeSessionId, content }, {
      onSettled: () => setIsTyping(false),
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setMessageInput(question);
    handleSendMessage();
  };

  const handleNewSession = () => {
    if (newSessionTenderId) {
      createSessionMutation.mutate(newSessionTenderId);
    }
  };

  if (sessionsLoading) {
    return (
      <div className="h-[calc(100vh-200px)] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 border-b">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">AI Assistant</h1>
          <Badge variant="outline" className="ml-2">
            <Sparkles className="mr-1 h-3 w-3" />
            RAG Enabled
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Dialog open={showNewSessionDialog} onOpenChange={setShowNewSessionDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Chat
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Start New Chat Session</DialogTitle>
                <DialogDescription>Select a tender to chat about</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Select value={newSessionTenderId} onValueChange={setNewSessionTenderId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a tender..." />
                  </SelectTrigger>
                  <SelectContent>
                    {tenders?.map(tender => (
                      <SelectItem key={tender.id} value={tender.id}>
                        {tender.title} ({tender.reference_number})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNewSessionDialog(false)}>Cancel</Button>
                <Button onClick={handleNewSession} disabled={!newSessionTenderId || createSessionMutation.isPending}>
                  {createSessionMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : 'Start Chat'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Sessions List */}
        <div className="w-72 flex-shrink-0 border-r bg-card flex flex-col hidden lg:flex">
          <div className="p-4 border-b">
            <h3 className="font-semibold mb-3">Chat History</h3>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
              {sessions?.map(session => (
                <div
                  key={session.id}
                  className={cn(
                    'p-3 rounded-lg cursor-pointer transition-colors',
                    activeSessionId === session.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-accent text-accent-foreground'
                  )}
                  onClick={() => setActiveSessionId(session.id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{session.title || 'Untitled Chat'}</p>
                      <p className="text-xs opacity-70 truncate">
                        {session.tender?.title || 'No tender linked'}
                      </p>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity">
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setActiveSessionId(session.id); }}>
                          <MessageSquare className="mr-2 h-3 w-3" />
                          Open
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); deleteSessionMutation.mutate(session.id); }} className="text-destructive">
                          <Trash2 className="mr-2 h-3 w-3" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <p className="text-xs opacity-60 mt-1">
                    {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })}
                  </p>
                </div>
              ))}
              {sessions?.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="mx-auto h-12 w-12 mb-3 opacity-30" />
                  <p className="text-sm">No chat sessions yet</p>
                  <p className="text-xs">Click "New Chat" to start</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {activeSession ? (
            <>
              {/* Session Header */}
              <div className="p-4 border-b bg-card">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-semibold">{activeSession.title || 'Untitled Chat'}</h2>
                    <p className="text-sm text-muted-foreground">
                      {activeSession.tender?.title ? `Context: ${activeSession.tender.title}` : 'No tender context'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="capitalize">{activeSession.status}</Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => deleteSessionMutation.mutate(activeSession.id)} className="text-destructive">
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete Session
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <ScrollArea className="flex-1 p-4 space-y-6">
                {messagesLoading ? (
                  <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="flex gap-3">
                        <Skeleton className="h-8 w-8 rounded-full" />
                        <div className="flex-1 space-y-2">
                          <Skeleton className="h-4 w-1/4" />
                          <Skeleton className="h-12 w-full" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : messages?.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                    <MessageSquare className="h-16 w-16 mb-4 opacity-30" />
                    <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
                    <p className="mb-6 max-w-md">Ask questions about the tender, get compliance checks, or generate proposal content.</p>
                    <div className="grid gap-2 sm:grid-cols-2 max-w-md">
                      {SUGGESTED_QUESTIONS.map((q, i) => (
                        <Button
                          key={i}
                          variant="outline"
                          className="justify-start text-sm h-auto p-3"
                          onClick={() => handleSuggestedQuestion(q)}
                        >
                          {q}
                        </Button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <>
                    {messages?.map((message, index) => (
                      <div
                        key={message.id}
                        className={cn(
                          'flex gap-3 animate-fade-in',
                          message.role === 'user' && 'flex-row-reverse'
                        )}
                      >
                        <Avatar className={cn('h-8 w-8 flex-shrink-0', message.role === 'user' ? 'bg-primary' : 'bg-secondary')}>
                          <AvatarFallback>
                            {message.role === 'user' ? 'U' : 'AI'}
                          </AvatarFallback>
                        </Avatar>
                        <div className={cn('flex-1 max-w-3xl', message.role === 'user' ? 'text-right' : '')}>
                          <div className={cn(
                            'inline-block max-w-[80%] px-4 py-2 rounded-2xl',
                            message.role === 'user'
                              ? 'bg-primary text-primary-foreground rounded-br-none'
                              : 'bg-muted rounded-bl-none'
                          )}>
                            {editingMessageId === message.id ? (
                              <div className="space-y-2">
                                <Textarea
                                  ref={textareaRef}
                                  value={editedContent}
                                  onChange={(e) => setEditedContent(e.target.value)}
                                  rows={3}
                                  className="min-w-[300px]"
                                />
                                <div className="flex justify-end gap-2">
                                  <Button variant="ghost" size="sm" onClick={() => setEditingMessageId(null)}>Cancel</Button>
                                  <Button size="sm" onClick={() => updateMessageMutation.mutate({ id: message.id, content: editedContent })}>
                                    Save
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                                {message.content}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1 opacity-60">
                            <span className="text-xs">{format(new Date(message.created_at), 'HH:mm')}</span>
                            {message.role === 'assistant' && (
                              <>
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" className="h-6 w-6 p-0" onClick={() => navigator.clipboard.writeText(message.content)}>
                                        <Copy className="h-3 w-3" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Copy</TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" className="h-6 w-6 p-0" onClick={() => setEditedContent(message.content) || setEditingMessageId(message.id)}>
                                        <Edit className="h-3 w-3" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Edit</TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" className="h-6 w-6 p-0">
                                        <ThumbsUp className="h-3 w-3" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Helpful</TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" className="h-6 w-6 p-0">
                                        <ThumbsDown className="h-3 w-3" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Not helpful</TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </>
                )}

                {isTyping && (
                  <div className="flex gap-3 animate-pulse">
                    <Avatar className="h-8 w-8 bg-secondary">
                      <AvatarFallback>AI</AvatarFallback>
                    </Avatar>
                    <div className="bg-muted rounded-2xl rounded-bl-none px-4 py-2 max-w-[80%]">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
              </ScrollArea>

              {/* Input Area */}
              <div className="p-4 border-t bg-card">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <Textarea
                    ref={textareaRef}
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about the tender, request compliance check, or generate content..."
                    rows={1}
                    className="flex-1 min-h-[44px] max-h-32 resize-none"
                    disabled={isTyping || !activeSessionId}
                  />
                  <Button
                    type="submit"
                    size="lg"
                    disabled={!messageInput.trim() || isTyping || !activeSessionId}
                    loading={isTyping}
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </form>
                <p className="text-xs text-muted-foreground text-center mt-2">
                  Press Enter to send, Shift+Enter for new line. AI responses are grounded in tender documents.
                </p>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground">
              <MessageSquare className="h-16 w-16 mb-4 opacity-30" />
              <h3 className="text-xl font-medium mb-2">Select or create a chat session</h3>
              <p className="max-w-md">Choose a session from the sidebar or start a new chat with a tender context.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}