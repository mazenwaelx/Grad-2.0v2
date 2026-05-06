using LawyerConnect.DTOs;
using System.ComponentModel.DataAnnotations;

namespace LawyerConnect.DTOs
{
    //wrapping for 2 dto registration 
    public class RegisterRequestDto
    {
        [Required(ErrorMessage = "User information is required")] // for run time validation Api request validation 
        public required UserRegisterDto User { get; set; } = null!; // (null!) compiler shutup (required for validating in compile/build - Time)
        
        public LawyerRegisterDto? Lawyer { get; set; } // optional 
    }
}