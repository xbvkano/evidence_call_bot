/*
  Warnings:

  - You are about to drop the column `blinds` on the `FormData` table. All the data in the column will be lost.
  - Added the required column `carpetShampooRooms` to the `FormData` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "FormData" DROP COLUMN "blinds",
ADD COLUMN     "carpetShampooRooms" INTEGER NOT NULL;
