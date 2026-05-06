import type {
  AuthResponseDto,
  LoginDto,
  RegisterRequestDto,
  LawyerRegisterDto,
  LawyerResponseDto,
  BookingDto,
  BookingResponseDto,
  ReviewCreateDto,
  ReviewResponseDto,
  NotificationResponseDto,
  PaymentSessionResponseDto,
  PaymentDto,
  ChatRoomResponseDto,
  ChatMessageResponseDto,
  SpecializationDto,
  InteractionTypeDto,
  LawyerPricingDto,
  UserResponseDto,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5128/api';

// Request deduplication cache for GET requests
const pendingRequests = new Map<string, Promise<any>>();

// Static data cache (specializations, interaction types)
const staticCache = new Map<string, { data: any; timestamp: number }>();
const STATIC_CACHE_TTL = 30 * 60 * 1000; // 30 minutes

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getAuthToken(): string | null {
    return localStorage.getItem('authToken');
  }

  private getHeaders(contentType: string = 'application/json'): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': contentType,
    };

    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const method = options.method || 'GET';
    const cacheKey = `${method}:${url}`;

    // Request deduplication for GET requests only
    if (method === 'GET') {
      // Check static cache first
      if (endpoint.includes('/specializations') || endpoint.includes('/interactiontypes')) {
        const cached = staticCache.get(endpoint);
        if (cached && Date.now() - cached.timestamp < STATIC_CACHE_TTL) {
          return cached.data as T;
        }
      }

      // Check if request is already pending
      if (pendingRequests.has(cacheKey)) {
        return pendingRequests.get(cacheKey) as Promise<T>;
      }
    }

    const requestPromise = (async () => {
      try {
        const response = await fetch(url, {
          ...options,
          headers: this.getHeaders(),
        });

        if (!response.ok) {
          let errorMessage = `API Error: ${response.status} ${response.statusText}`;
          
          try {
            const errorData = await response.json();
            if (errorData.errors && Array.isArray(errorData.errors)) {
              // Handle validation errors array
              errorMessage = errorData.errors.join(', ');
            } else if (errorData.errors && typeof errorData.errors === 'object') {
              // Handle ASP.NET validation errors object: { field: [msg1, msg2] }
              const validationMessages = Object.values(errorData.errors)
                .flat()
                .filter((msg): msg is string => typeof msg === 'string');
              if (validationMessages.length > 0) {
                errorMessage = validationMessages.join(', ');
              }
            } else if (errorData.message) {
              errorMessage = errorData.message;
            } else if (errorData.title) {
              errorMessage = errorData.title;
            } else if (typeof errorData === 'string') {
              errorMessage = errorData;
            }
          } catch {
            // Fallback for plain text error bodies
            try {
              const textError = await response.text();
              if (textError) errorMessage = textError;
            } catch {
              // Keep default error message
            }
          }
          
          throw new Error(errorMessage);
        }

        if (response.status === 204) {
          return {} as T;
        }

        const data = await response.json() as T;

        // Cache static data
        if (method === 'GET' && (endpoint.includes('/specializations') || endpoint.includes('/interactiontypes'))) {
          staticCache.set(endpoint, { data, timestamp: Date.now() });
        }

        return data;
      } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
      } finally {
        // Remove from pending requests
        if (method === 'GET') {
          pendingRequests.delete(cacheKey);
        }
      }
    })();

    // Store pending GET request
    if (method === 'GET') {
      pendingRequests.set(cacheKey, requestPromise);
    }

    return requestPromise;
  }

  // ==================== AUTH ====================

  async registerUser(data: RegisterRequestDto): Promise<AuthResponseDto> {
    return this.request<AuthResponseDto>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(data: LoginDto): Promise<AuthResponseDto> {
    return this.request<AuthResponseDto>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me', {
      method: 'GET',
    });
  }

  // ==================== LAWYERS ====================

  async registerLawyer(data: LawyerRegisterDto): Promise<LawyerResponseDto> {
    return this.request<LawyerResponseDto>('/lawyers/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getLawyers(page: number = 1, limit: number = 10): Promise<LawyerResponseDto[]> {
    return this.request<LawyerResponseDto[]>(
      `/lawyers?page=${page}&limit=${limit}`,
      { method: 'GET' }
    );
  }

  async getFeaturedLawyers(limit: number = 3): Promise<LawyerResponseDto[]> {
    return this.request<LawyerResponseDto[]>(
      `/lawyers/featured?limit=${limit}`,
      { method: 'GET' }
    );
  }

  async getLawyer(id: number): Promise<LawyerResponseDto> {
    return this.request<LawyerResponseDto>(`/lawyers/${id}`, {
      method: 'GET',
    });
  }

  async getLawyerById(id: number): Promise<LawyerResponseDto> {
    return this.request<LawyerResponseDto>(`/lawyers/${id}`, {
      method: 'GET',
    });
  }

  async getMyLawyerProfile(): Promise<LawyerResponseDto> {
    return this.request<LawyerResponseDto>('/lawyers/me', {
      method: 'GET',
    });
  }

  async getLawyerPricing(lawyerId: number): Promise<LawyerPricingDto[]> {
    return this.request<LawyerPricingDto[]>(`/lawyers/${lawyerId}/pricing`, {
      method: 'GET',
    });
  }

  async setLawyerPricing(lawyerId: number, data: LawyerPricingDto): Promise<LawyerPricingDto> {
    return this.request<LawyerPricingDto>(`/lawyers/${lawyerId}/pricing`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateLawyerPricing(lawyerId: number, data: LawyerPricingDto): Promise<void> {
    return this.request<void>(`/lawyers/${lawyerId}/pricing`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteLawyerPricing(lawyerId: number, specializationId: number, interactionTypeId: number): Promise<void> {
    return this.request<void>(`/lawyers/${lawyerId}/pricing/${specializationId}/${interactionTypeId}`, {
      method: 'DELETE',
    });
  }

  async searchLawyers(filters: Record<string, string | number>): Promise<LawyerResponseDto[]> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, val]) => {
      if (val !== undefined && val !== '') params.append(key, String(val));
    });
    return this.request<LawyerResponseDto[]>(`/lawyers/search?${params.toString()}`, { method: 'GET' });
  }

  // ==================== BOOKINGS ====================

  async createBooking(data: BookingDto): Promise<BookingResponseDto> {
    return this.request<BookingResponseDto>('/bookings', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getBooking(id: number): Promise<BookingResponseDto> {
    return this.request<BookingResponseDto>(`/bookings/${id}`, {
      method: 'GET',
    });
  }

  async getUserBookings(): Promise<BookingResponseDto[]> {
    return this.request<BookingResponseDto[]>('/bookings/user', {
      method: 'GET',
    });
  }

  async getLawyerBookings(): Promise<BookingResponseDto[]> {
    return this.request<BookingResponseDto[]>('/bookings/lawyer', {
      method: 'GET',
    });
  }

  async getLawyerAppointments(): Promise<BookingResponseDto[]> {
    return this.request<BookingResponseDto[]>('/bookings/lawyer', {
      method: 'GET',
    });
  }

  async updateBookingStatus(id: number, status: string): Promise<void> {
    return this.request<void>(`/bookings/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify(status),
    });
  }

  // ==================== REVIEWS ====================

  async createReview(data: ReviewCreateDto): Promise<ReviewResponseDto> {
    return this.request<ReviewResponseDto>('/reviews', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getLawyerReviews(lawyerId: number, page: number = 1, limit: number = 10): Promise<ReviewResponseDto[]> {
    return this.request<ReviewResponseDto[]>(`/reviews/lawyer/${lawyerId}?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  async getLawyerRating(lawyerId: number): Promise<{ averageRating: number }> {
    return this.request<{ averageRating: number }>(`/reviews/lawyer/${lawyerId}/rating`, {
      method: 'GET',
    });
  }

  async getFeaturedReviews(limit: number = 3): Promise<ReviewResponseDto[]> {
    return this.request<ReviewResponseDto[]>(`/reviews/featured?limit=${limit}`, {
      method: 'GET',
    });
  }

  // ==================== CHAT ====================

  async getChatRoom(bookingId: number): Promise<ChatRoomResponseDto> {
    return this.request<ChatRoomResponseDto>(`/chat/${bookingId}`, {
      method: 'GET',
    });
  }

  async getChatMessages(bookingId: number, page: number = 1, limit: number = 50): Promise<ChatMessageResponseDto[]> {
    return this.request<ChatMessageResponseDto[]>(`/chat/${bookingId}/messages?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  async sendChatMessage(bookingId: number, message: string): Promise<ChatMessageResponseDto> {
    return this.request<ChatMessageResponseDto>(`/chat/${bookingId}/messages`, {
      method: 'POST',
      body: JSON.stringify(message),
    });
  }

  // ==================== PAYMENTS ====================

  async createPaymentSession(data: PaymentDto): Promise<PaymentSessionResponseDto> {
    return this.request<PaymentSessionResponseDto>('/payments/create-session', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async confirmPayment(sessionId: number): Promise<PaymentSessionResponseDto> {
    return this.request<PaymentSessionResponseDto>('/payments/confirm', {
      method: 'POST',
      body: JSON.stringify({ sessionId, providerSessionId: '' }),
    });
  }

  async getPaymentSession(id: number): Promise<PaymentSessionResponseDto> {
    return this.request<PaymentSessionResponseDto>(`/payments/${id}`, {
      method: 'GET',
    });
  }

  async getUserPayments(page: number = 1, limit: number = 10): Promise<PaymentSessionResponseDto[]> {
    return this.request<PaymentSessionResponseDto[]>(`/payments/user?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  // ==================== NOTIFICATIONS ====================

  async getNotifications(page: number = 1, limit: number = 20): Promise<NotificationResponseDto[]> {
    return this.request<NotificationResponseDto[]>(`/notifications?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  async getUnreadCount(): Promise<{ unreadCount: number }> {
    return this.request<{ unreadCount: number }>('/notifications/unread-count', {
      method: 'GET',
    });
  }

  async markNotificationRead(id: number): Promise<void> {
    return this.request<void>(`/notifications/${id}/read`, {
      method: 'PUT',
    });
  }

  async markAllNotificationsRead(): Promise<void> {
    return this.request<void>('/notifications/mark-all-read', {
      method: 'PUT',
    });
  }

  async deleteNotification(id: number): Promise<void> {
    return this.request<void>(`/notifications/${id}`, {
      method: 'DELETE',
    });
  }

  // ==================== SPECIALIZATIONS ====================

  async getSpecializations(): Promise<SpecializationDto[]> {
    return this.request<SpecializationDto[]>('/specializations', {
      method: 'GET',
    });
  }

  async getInteractionTypes(): Promise<InteractionTypeDto[]> {
    return this.request<InteractionTypeDto[]>('/interactiontypes', {
      method: 'GET',
    });
  }

  // ==================== ADMIN ====================

  async adminGetAllUsers(page: number = 1, limit: number = 20): Promise<UserResponseDto[]> {
    return this.request<UserResponseDto[]>(`/admin/users?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  async adminGetPendingLawyers(page: number = 1, limit: number = 20): Promise<LawyerResponseDto[]> {
    return this.request<LawyerResponseDto[]>(`/admin/lawyers/pending?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  async adminVerifyLawyer(id: number): Promise<void> {
    return this.request<void>(`/admin/lawyers/${id}/verify`, {
      method: 'PUT',
    });
  }

  async adminRejectLawyer(id: number, reason: string): Promise<void> {
    return this.request<void>(`/admin/lawyers/${id}/reject`, {
      method: 'PUT',
      body: JSON.stringify({ reason }),
    });
  }

  async adminSuspendUser(id: number): Promise<void> {
    return this.request<void>(`/admin/users/${id}/suspend`, {
      method: 'PUT',
    });
  }

  async adminUnsuspendUser(id: number): Promise<void> {
    return this.request<void>(`/admin/users/${id}/unsuspend`, {
      method: 'PUT',
    });
  }

  async adminGetAllBookings(page: number = 1, limit: number = 20): Promise<BookingResponseDto[]> {
    return this.request<BookingResponseDto[]>(`/admin/bookings?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  async adminGetAllPayments(page: number = 1, limit: number = 20): Promise<PaymentSessionResponseDto[]> {
    return this.request<PaymentSessionResponseDto[]>(`/admin/payments?page=${page}&limit=${limit}`, {
      method: 'GET',
    });
  }

  // ==================== USER PROFILE ====================

  async uploadProfilePhoto(photoBase64: string): Promise<{ profilePhoto: string }> {
    return this.request<{ profilePhoto: string }>('/users/upload-photo', {
      method: 'PUT',
      body: JSON.stringify({ photoBase64 }),
    });
  }

  async removeProfilePhoto(): Promise<void> {
    return this.request<void>('/users/remove-photo', {
      method: 'DELETE',
    });
  }

  // ==================== CACHE MANAGEMENT ====================

  clearStaticCache(): void {
    staticCache.clear();
  }

  clearAllCaches(): void {
    staticCache.clear();
    pendingRequests.clear();
    sessionStorage.removeItem('lawyers_cache');
    sessionStorage.removeItem('lawyers_cache_timestamp');
    sessionStorage.removeItem('user_bookings_cache');
    sessionStorage.removeItem('user_bookings_cache_timestamp');
    sessionStorage.removeItem('lawyer_bookings_cache');
    sessionStorage.removeItem('lawyer_bookings_cache_timestamp');
  }
}

export const apiService = new ApiService();
export default ApiService;
