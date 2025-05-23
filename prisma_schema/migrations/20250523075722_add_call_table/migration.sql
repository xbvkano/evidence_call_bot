-- CreateTable
CREATE TABLE "Call" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "caller" TEXT NOT NULL,
    "called" TEXT NOT NULL,
    "size" TEXT NOT NULL,
    "service" TEXT NOT NULL,
    "section" TEXT NOT NULL,

    CONSTRAINT "Call_pkey" PRIMARY KEY ("id")
);
