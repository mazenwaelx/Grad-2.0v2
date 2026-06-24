namespace LawyerConnect.DTOs
{
    public class PaymentDto
    {
        public int BookingId { get; set; }
        public decimal Amount { get; set; }
        public string Provider { get; set; }="";
    }
}

