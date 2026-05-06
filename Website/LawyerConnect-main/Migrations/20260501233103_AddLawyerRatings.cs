using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace LawyerConnect.Migrations
{
    /// <inheritdoc />
    public partial class AddLawyerRatings : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<decimal>(
                name: "AverageRating",
                table: "Lawyers",
                type: "decimal(18,2)",
                nullable: false,
                defaultValue: 0m);

            migrationBuilder.AddColumn<int>(
                name: "ReviewsCount",
                table: "Lawyers",
                type: "int",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<bool>(
                name: "IsArchived",
                table: "ChatRooms",
                type: "bit",
                nullable: false,
                defaultValue: false);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "AverageRating",
                table: "Lawyers");

            migrationBuilder.DropColumn(
                name: "ReviewsCount",
                table: "Lawyers");

            migrationBuilder.DropColumn(
                name: "IsArchived",
                table: "ChatRooms");
        }
    }
}
