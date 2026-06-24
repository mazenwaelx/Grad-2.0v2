using LawyerConnect.DTOs;
using System.Text;
using System.Text.Json;

namespace LawyerConnect.Services
{
    public class AIChatService : IAIChatService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<AIChatService> _logger;
        private readonly string _aiApiBaseUrl;

        public AIChatService(IHttpClientFactory httpClientFactory, IConfiguration configuration, ILogger<AIChatService> logger)
        {
            _httpClient = httpClientFactory.CreateClient("AIBackend");
            _logger = logger;
            _aiApiBaseUrl = configuration["AIBackend:BaseUrl"] ?? "http://localhost:8000";
        }

        public async Task<AIChatResponseDto> SendMessageAsync(string message, string userId, string chatId)
        {
            try
            {
                var request = new
                {
                    message,
                    chat_id = chatId,
                    user_id = userId
                };

                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync($"{_aiApiBaseUrl}/api/chat", content);
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync();
                var aiResponse = JsonSerializer.Deserialize<AIChatResponseDto>(responseJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                return aiResponse ?? new AIChatResponseDto { Response = "Error processing response" };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error communicating with AI backend");
                throw;
            }
        }

        public async Task<List<AIChatHistoryDto>> GetUserChatsAsync(string userId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_aiApiBaseUrl}/api/chats/{userId}");
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<PythonChatsWrapper>(responseJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                // Map Python format to C# format
                var chats = new List<AIChatHistoryDto>();
                
                if (result?.Chats != null)
                {
                    foreach (var chat in result.Chats)
                    {
                        chats.Add(new AIChatHistoryDto
                        {
                            ChatId = chat.ChatId ?? string.Empty,
                            Title = chat.Title ?? "New Chat",
                            CreatedAt = chat.CreatedAt,
                            UpdatedAt = chat.UpdatedAt
                        });
                    }
                }

                return chats;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving user chats from AI backend");
                return new List<AIChatHistoryDto>();
            }
        }

        public async Task<List<AIChatMessageDto>> GetChatMessagesAsync(string chatId, string userId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_aiApiBaseUrl}/api/messages/{chatId}");
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<PythonMessagesWrapper>(responseJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                // Map Python format (role/content) to C# format (sender/text)
                var messages = new List<AIChatMessageDto>();
                int id = 1;
                
                if (result?.Messages != null)
                {
                    foreach (var msg in result.Messages)
                    {
                        messages.Add(new AIChatMessageDto
                        {
                            Id = id++,
                            Text = msg.Content ?? string.Empty,
                            Sender = msg.Role == "user" ? "user" : "ai",
                            Timestamp = msg.CreatedAt
                        });
                    }
                }

                return messages;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving chat messages from AI backend");
                return new List<AIChatMessageDto>();
            }
        }

        public async Task DeleteChatAsync(string chatId, string userId)
        {
            try
            {
                var response = await _httpClient.DeleteAsync($"{_aiApiBaseUrl}/api/chat/{userId}/{chatId}");
                response.EnsureSuccessStatusCode();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting chat from AI backend");
                throw;
            }
        }

        public async Task<FileUploadResponseDto> UploadFileAsync(IFormFile file)
        {
            try
            {
                using var formData = new MultipartFormDataContent();
                using var fileStream = file.OpenReadStream();
                using var streamContent = new StreamContent(fileStream);
                
                formData.Add(streamContent, "file", file.FileName);

                var response = await _httpClient.PostAsync($"{_aiApiBaseUrl}/api/upload", formData);
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<FileUploadResponseDto>(responseJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                return result ?? new FileUploadResponseDto { Success = false, Message = "Unknown error" };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error uploading file to AI backend");
                throw;
            }
        }

        public async Task<List<UploadedFileDto>> GetUploadedFilesAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_aiApiBaseUrl}/api/files");
                response.EnsureSuccessStatusCode();

                var responseJson = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<FilesWrapper>(responseJson, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                return result?.Files ?? new List<UploadedFileDto>();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving files from AI backend");
                return new List<UploadedFileDto>();
            }
        }

        public async Task DeleteFileAsync(string fileHash)
        {
            try
            {
                var response = await _httpClient.DeleteAsync($"{_aiApiBaseUrl}/api/files/{fileHash}");
                response.EnsureSuccessStatusCode();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting file from AI backend");
                throw;
            }
        }

        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_aiApiBaseUrl}/api/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        // Helper classes for deserialization
        private class PythonChat
        {
            public string ChatId { get; set; } = string.Empty;
            public string Title { get; set; } = string.Empty;
            public DateTime CreatedAt { get; set; }
            public DateTime UpdatedAt { get; set; }
        }

        private class PythonChatsWrapper
        {
            public List<PythonChat> Chats { get; set; } = new();
        }

        private class PythonMessage
        {
            public string Role { get; set; } = string.Empty;
            public string Content { get; set; } = string.Empty;
            public DateTime CreatedAt { get; set; }
        }

        private class PythonMessagesWrapper
        {
            public List<PythonMessage> Messages { get; set; } = new();
        }

        private class FilesWrapper
        {
            public List<UploadedFileDto> Files { get; set; } = new();
        }
    }
}
